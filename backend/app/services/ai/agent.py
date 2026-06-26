"""
The AI Agent.
This is the core autonomous loop that replaces manual follow-up sequences.

For every lead where next_action_at <= NOW():
  1. Gather full context (conversation, scores, org knowledge)
  2. Retrieve relevant RAG context
  3. Ask AI: what should happen next?
  4. Execute the decision
  5. Log everything
  6. Schedule next evaluation
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models import Lead, AIAction, Conversation, Message
from app.repositories.lead_repo import LeadRepository
from app.services.ai.groq_provider import get_ai_provider
from app.services.ai.rag import retrieve_relevant_context
from app.services.ai import prompts
from app.services.anti_spam import calculate_spam_risk
from app.services import email_service

logger = logging.getLogger(__name__)


def _format_conversation(lead: Lead) -> str:
    if not lead.conversation or not lead.conversation.messages:
        return "No messages yet."
    lines = []
    for msg in lead.conversation.messages[-10:]:  # last 10 messages
        role = "Lead" if msg.role == "lead" else "AI"
        lines.append(f"{role}: {msg.content[:500]}")
    return "\n\n".join(lines)


def _days_since(dt: datetime | None) -> int:
    if not dt:
        return 0
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


async def run_agent_for_lead(lead: Lead, db: AsyncSession) -> None:
    """Evaluate one lead and take appropriate action."""
    org = lead.organization
    if not org:
        return

    ai = get_ai_provider(settings.GROQ_API_KEY)

    # Anti-spam check first
    spam_risk = calculate_spam_risk(lead, org)
    if spam_risk >= 80:
        lead.spam_risk_score = spam_risk
        lead.status = "stopped"
        lead.stop_reason = f"Anti-spam: risk score {spam_risk}"
        lead.next_action_at = None
        db.add(AIAction(
            lead_id=lead.id, org_id=org.id,
            action_type="stop_outreach",
            reasoning=f"Spam risk score {spam_risk} — stopping outreach to protect email reputation",
        ))
        await db.flush()
        return

    # Retrieve relevant knowledge
    query = f"{lead.message or ''} {lead.company or ''} {lead.full_name or ''}"
    rag_context = await retrieve_relevant_context(query, org.id, db)

    # Build conversation string
    conversation_str = _format_conversation(lead)
    days_first = _days_since(lead.created_at)
    days_last = _days_since(lead.last_ai_action)

    # Step 1: Evaluate — ask AI what to do
    eval_messages = [
        prompts.build_system_message(org, rag_context),
        {
            "role": "user",
            "content": prompts.evaluate_lead_prompt(
                full_name=lead.full_name or "",
                company=lead.company or "",
                original_message=lead.message or "",
                followup_count=lead.followup_count,
                days_since_first=days_first,
                days_since_last=days_last,
                intent_score=lead.intent_score,
                sentiment=lead.sentiment or "unknown",
                conversation_history=conversation_str,
                max_attempts=org.max_followup_attempts,
            )
        }
    ]

    try:
        eval_response = await ai.complete(eval_messages, "evaluate_lead", temperature=0.3, max_tokens=500)
        raw = eval_response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        evaluation = json.loads(raw.strip())
    except Exception as e:
        logger.error(f"Agent evaluation failed for lead {lead.id}: {e}")
        # Retry in 2 hours
        lead.next_action_at = datetime.now(timezone.utc) + timedelta(hours=2)
        await db.flush()
        return

    decision = evaluation.get("decision", "wait_longer")
    reasoning = evaluation.get("reasoning", "")
    next_hours = evaluation.get("next_action_hours", 24)
    updated_scores = evaluation.get("updated_scores", {})

    # Update scores
    if updated_scores:
        lead.intent_score = updated_scores.get("intent_score", lead.intent_score)
        lead.urgency_score = updated_scores.get("urgency_score", lead.urgency_score)
        lead.buying_probability = updated_scores.get("buying_probability", lead.buying_probability)
        lead.sentiment = updated_scores.get("sentiment", lead.sentiment)
    lead.spam_risk_score = spam_risk

    # Step 2: Execute decision
    if decision == "stop_outreach":
        lead.status = "stopped"
        lead.stop_reason = evaluation.get("stop_reason") or reasoning
        lead.next_action_at = None
        db.add(AIAction(lead_id=lead.id, org_id=org.id, action_type="stop_outreach",
                        reasoning=reasoning, tokens_used=eval_response.tokens_used,
                        model_used="groq", latency_ms=eval_response.latency_ms))

    elif decision == "escalate_human":
        lead.human_takeover = True
        lead.status = "needs_human"
        lead.next_action_at = None
        db.add(AIAction(lead_id=lead.id, org_id=org.id, action_type="escalated_human",
                        reasoning=reasoning, tokens_used=eval_response.tokens_used,
                        model_used="groq"))
        # TODO: notify owner via email

    elif decision == "wait_longer":
        lead.next_action_at = datetime.now(timezone.utc) + timedelta(hours=next_hours)
        db.add(AIAction(lead_id=lead.id, org_id=org.id, action_type="wait",
                        reasoning=reasoning, tokens_used=eval_response.tokens_used,
                        model_used="groq"))

    elif decision in ("send_followup", "propose_meeting"):
        push_meeting = decision == "propose_meeting"

        # Write the email
        write_messages = [
            prompts.build_system_message(org, rag_context),
            {
                "role": "user",
                "content": prompts.write_followup_prompt(
                    full_name=lead.full_name or "",
                    company=lead.company or "",
                    original_message=lead.message or "",
                    followup_count=lead.followup_count,
                    reasoning=reasoning,
                    tone=org.ai_tone,
                    conversation_history=conversation_str,
                    push_for_meeting=push_meeting,
                )
            }
        ]
        write_response = await ai.complete(write_messages, "write_followup", temperature=0.75, max_tokens=600)
        email_body = write_response.content.strip()

        # Determine subject
        if lead.followup_count == 0:
            subject = f"Re: Your inquiry to {org.name}"
        else:
            subject = f"Following up — {org.name}"

        # Send email
        try:
            await email_service.send_lead_email(
                to_email=lead.email,
                lead_name=lead.full_name or lead.email,
                subject=subject,
                body=email_body,
                from_business=org.name,
            )
        except Exception as e:
            logger.error(f"Email send failed for lead {lead.id}: {e}")

        # Save message to conversation
        if lead.conversation:
            msg = Message(
                conversation_id=lead.conversation.id,
                role="ai",
                content=email_body,
                sent_via="email",
            )
            db.add(msg)

        # Update lead state
        lead.followup_count += 1
        lead.last_ai_action = datetime.now(timezone.utc)
        lead.next_action_at = datetime.now(timezone.utc) + timedelta(hours=next_hours)
        if lead.status == "new":
            lead.status = "ai_contacted"
        elif decision == "propose_meeting":
            lead.status = "meeting_proposed"

        action_type = "propose_meeting" if push_meeting else "followup"
        db.add(AIAction(
            lead_id=lead.id, org_id=org.id,
            action_type=action_type,
            reasoning=reasoning,
            response_content=email_body,
            tokens_used=(eval_response.tokens_used or 0) + (write_response.tokens_used or 0),
            model_used="groq",
            latency_ms=eval_response.latency_ms,
        ))

    await db.flush()
    logger.info(f"Agent decision for lead {lead.id}: {decision} | intent={lead.intent_score}")


async def run_agent_loop() -> None:
    """
    Called by APScheduler every 15 minutes.
    Processes all leads due for agent evaluation.
    """
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        try:
            lead_repo = LeadRepository(db)
            due_leads = await lead_repo.get_due_for_agent()
            logger.info(f"Agent loop: {len(due_leads)} leads to evaluate")

            for lead in due_leads:
                try:
                    await run_agent_for_lead(lead, db)
                except Exception as e:
                    logger.error(f"Agent failed for lead {lead.id}: {e}")
                    continue

            await db.commit()
        except Exception as e:
            logger.error(f"Agent loop error: {e}")
            await db.rollback()
        finally:
            await engine.dispose()


async def qualify_new_lead(lead_id: str, org_id: str, db_url: str) -> None:
    """
    Called via BackgroundTask immediately after form submission.
    Runs initial scoring + sends first response.
    """
    engine = create_async_engine(db_url, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        try:
            lead_repo = LeadRepository(db)
            lead = await lead_repo.get_with_details(lead_id)
            if not lead or not lead.organization:
                return

            org = lead.organization
            ai = get_ai_provider(settings.GROQ_API_KEY)

            # Step 1: Get RAG context
            query = f"{lead.message or ''} {lead.company or ''}"
            rag_context = await retrieve_relevant_context(query, org.id, db)

            # Step 2: Score the lead
            score_messages = [
                {"role": "system", "content": "You are a B2B sales qualification expert. Return only valid JSON."},
                {"role": "user", "content": prompts.score_lead_prompt(
                    message=lead.message or "",
                    company=lead.company or "",
                    rag_context=rag_context,
                )}
            ]
            score_response = await ai.complete(score_messages, "score_lead", temperature=0.2, max_tokens=400)

            try:
                raw = score_response.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                scores = json.loads(raw.strip())
                lead.intent_score = scores.get("intent_score", 30)
                lead.urgency_score = scores.get("urgency_score", 30)
                lead.buying_probability = scores.get("buying_probability", 30)
                lead.estimated_deal_value = scores.get("estimated_deal_value")
                lead.sentiment = scores.get("sentiment", "neutral")
                lead.detected_objections = scores.get("detected_objections", [])
                lead.qualification_summary = scores.get("qualification_summary", "")
                lead.recommended_action = scores.get("recommended_action", "")
                lead.risk_factors = scores.get("risk_factors", [])
            except Exception as e:
                logger.error(f"Score parsing failed: {e}")
                lead.intent_score = 30

            db.add(AIAction(lead_id=lead.id, org_id=org.id, action_type="scored",
                            reasoning="Initial lead scoring on submission",
                            tokens_used=score_response.tokens_used, model_used="groq"))

            # Step 3: Write initial response
            response_messages = [
                prompts.build_system_message(org, rag_context),
                {"role": "user", "content": prompts.initial_response_prompt(
                    full_name=lead.full_name or "",
                    company=lead.company or "",
                    message=lead.message or "",
                    tone=org.ai_tone,
                    rag_context=rag_context,
                )}
            ]
            response = await ai.complete(response_messages, "initial_response", temperature=0.75, max_tokens=600)
            email_body = response.content.strip()

            # Step 4: Send email
            await email_service.send_lead_email(
                to_email=lead.email,
                lead_name=lead.full_name or lead.email,
                subject=f"Re: Your inquiry to {org.name}",
                body=email_body,
                from_business=org.name,
            )

            # Step 5: Save message
            if lead.conversation:
                db.add(Message(
                    conversation_id=lead.conversation.id,
                    role="lead",
                    content=lead.message or "(form submission)",
                    sent_via="form",
                ))
                db.add(Message(
                    conversation_id=lead.conversation.id,
                    role="ai",
                    content=email_body,
                    sent_via="email",
                ))

            db.add(AIAction(lead_id=lead.id, org_id=org.id, action_type="initial_response",
                            response_content=email_body,
                            tokens_used=response.tokens_used, model_used="groq"))

            # Step 6: Update lead state + schedule next agent evaluation
            lead.status = "ai_contacted"
            lead.followup_count = 0
            lead.last_ai_action = datetime.now(timezone.utc)

            # Schedule first agent evaluation based on intent
            if lead.intent_score >= 70:
                hours_until_next = 24   # hot lead — check tomorrow
            elif lead.intent_score >= 40:
                hours_until_next = 48   # warm — check in 2 days
            else:
                hours_until_next = 72   # cold — check in 3 days

            lead.next_action_at = datetime.now(timezone.utc) + timedelta(hours=hours_until_next)

            await db.commit()
            logger.info(f"Lead {lead_id} qualified: intent={lead.intent_score}, next_action in {hours_until_next}h")

        except Exception as e:
            logger.error(f"Initial qualification failed for lead {lead_id}: {e}")
            await db.rollback()
        finally:
            await engine.dispose()
