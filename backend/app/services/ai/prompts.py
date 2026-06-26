"""All AI prompt templates. Edit here only — never inline in services."""


def agent_system(business_name: str, description: str, services: str,
                 pricing: str, rules: str, tone: str, rag_context: str) -> str:
    return f"""You are an AI sales representative for {business_name}.

ABOUT THE BUSINESS:
{description}

SERVICES OFFERED:
{services}

PRICING GUIDANCE:
{pricing or "Pricing discussed on discovery call"}

BUSINESS RULES (follow strictly):
{rules or "Be honest, professional, and helpful."}

RELEVANT KNOWLEDGE FROM WEBSITE/DOCS:
{rag_context or "No additional context available."}

YOUR COMMUNICATION STYLE: {tone}

IMPORTANT:
- Never promise specific outcomes or guarantees
- Never invent pricing or features not listed above
- Never be pushy or aggressive
- Always focus on understanding the lead's needs first
- You represent {business_name} — protect their reputation
"""


def score_lead_prompt(message: str, company: str, rag_context: str) -> str:
    return f"""Analyze this inbound lead and score them.

Lead's message: {message or "No message provided"}
Company: {company or "Unknown"}

Relevant business context:
{rag_context}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "intent_score": <0-100>,
  "urgency_score": <0-100>,
  "buying_probability": <0-100>,
  "estimated_deal_value": <number or null>,
  "sentiment": "<positive|neutral|negative>",
  "detected_objections": ["<objection1>", "<objection2>"],
  "qualification_summary": "<2-3 sentences for the sales team>",
  "recommended_action": "<one sentence next step>",
  "risk_factors": ["<risk1>", "<risk2>"]
}}"""


def initial_response_prompt(full_name: str, company: str, message: str,
                             tone: str, rag_context: str) -> str:
    return f"""Write a first response email to this new lead.

Lead name: {full_name or "there"}
Company: {company or "their company"}
Their message: {message or "They submitted a contact form without a message."}

Relevant knowledge to reference:
{rag_context}

Guidelines:
- Acknowledge their SPECIFIC situation or need
- Show genuine understanding (not generic)
- Ask 1-2 thoughtful qualifying questions
- Warm, natural invitation to have a conversation (not pushy)
- Tone: {tone}
- 2-3 short paragraphs maximum
- Do NOT include subject line
- Do NOT include a sign-off name (system adds it)
- Write only the email body"""


def evaluate_lead_prompt(full_name: str, company: str, original_message: str,
                          followup_count: int, days_since_first: int,
                          days_since_last: int, intent_score: int,
                          sentiment: str, conversation_history: str,
                          max_attempts: int) -> str:
    return f"""Evaluate this lead and decide what to do next.

LEAD: {full_name or "Unknown"} from {company or "unknown company"}
Original message: {original_message or "N/A"}
Follow-ups sent: {followup_count} (max allowed: {max_attempts})
Days since first contact: {days_since_first}
Days since last message: {days_since_last}
Current intent score: {intent_score}/100
Current sentiment: {sentiment or "unknown"}

CONVERSATION HISTORY:
{conversation_history}

DECISION OPTIONS:
- send_followup: lead is still potentially interested, send another message
- propose_meeting: lead shows strong buying signals, push for a call
- stop_outreach: max attempts reached, or lead clearly not interested
- escalate_human: situation is complex, unusual, or needs human judgment
- wait_longer: too soon to follow up again, check back later

Return ONLY valid JSON:
{{
  "decision": "<send_followup|propose_meeting|stop_outreach|escalate_human|wait_longer>",
  "reasoning": "<1-2 sentences explaining why>",
  "next_action_hours": <hours until next evaluation, e.g. 24 or 72>,
  "updated_scores": {{
    "intent_score": <0-100>,
    "urgency_score": <0-100>,
    "buying_probability": <0-100>,
    "sentiment": "<positive|neutral|negative>"
  }},
  "stop_reason": "<reason if stopping, else null>"
}}"""


def write_followup_prompt(full_name: str, company: str, original_message: str,
                           followup_count: int, reasoning: str, tone: str,
                           conversation_history: str, push_for_meeting: bool) -> str:
    meeting_instruction = (
        "Propose scheduling a brief discovery call — include a direct invitation."
        if push_for_meeting else
        "Do NOT push hard for a meeting yet — focus on being helpful first."
    )
    return f"""Write follow-up email #{followup_count + 1} to this lead.

Lead: {full_name or "there"} from {company or "their company"}
Original inquiry: {original_message or "N/A"}
Why you're following up: {reasoning}

Previous conversation:
{conversation_history}

Guidelines:
- Reference something SPECIFIC from their situation or previous messages
- Natural, human tone — not robotic or templated
- {meeting_instruction}
- Maximum 3 short paragraphs
- Tone: {tone}
- No subject line, no sign-off name
- Write only the email body"""


def propose_meeting_prompt(full_name: str, company: str, tone: str,
                            booking_link: str, conversation_summary: str) -> str:
    return f"""Write an email proposing a discovery call to this high-intent lead.

Lead: {full_name or "there"} from {company or "their company"}
Conversation summary: {conversation_summary}

Booking link: {booking_link}

Guidelines:
- Acknowledge the conversation so far
- Make a confident, clear invitation for a discovery call
- Include the booking link naturally in the message
- Keep it short and direct (2 paragraphs max)
- Tone: {tone}
- No subject line, no sign-off name
- Write only the email body"""


def build_system_message(org, rag_context: str) -> dict:
    return {
        "role": "system",
        "content": agent_system(
            business_name=org.name,
            description=org.description or "",
            services=org.services or "",
            pricing=org.pricing_guidance or "",
            rules=org.business_rules or "",
            tone=org.ai_tone,
            rag_context=rag_context,
        )
    }
