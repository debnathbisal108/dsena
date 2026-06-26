from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.config import settings
from app.middleware.rate_limit import limiter
from app.repositories.lead_repo import LeadRepository, KnowledgeRepository
from app.repositories.user_repo import OrgRepository
from app.schemas import DashboardMetrics, LeadSubmitRequest, BookSlotRequest
from app.models import Lead, Conversation, Meeting
from app.services import calendar_service, email_service
from app.services.ai.agent import qualify_new_lead

# ── Knowledge ──────────────────────────────────────────────────────────────
knowledge_router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


async def get_user_org(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = await OrgRepository(db).get_by_owner(current_user.id)
    if not org:
        raise ForbiddenError("No organization found")
    return org


@knowledge_router.get("/chunks")
async def list_chunks(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = KnowledgeRepository(db)
    chunks = await repo.get_chunks_by_org(org.id)
    return [{"id": c.id, "source_type": c.source_type, "source_url": c.source_url,
             "title": c.title, "content": c.content[:200] + "..." if len(c.content) > 200 else c.content,
             "created_at": c.created_at} for c in chunks]


@knowledge_router.delete("/chunks/{chunk_id}", status_code=204)
async def delete_chunk(chunk_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = KnowledgeRepository(db)
    await repo.delete_chunk(chunk_id)


@knowledge_router.get("/documents")
async def list_documents(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = KnowledgeRepository(db)
    docs = await repo.get_documents(org.id)
    return [{"id": d.id, "filename": d.filename, "file_type": d.file_type,
             "status": d.status, "chunks_created": d.chunks_created, "created_at": d.created_at} for d in docs]


@knowledge_router.get("/crawl-jobs")
async def list_crawl_jobs(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = KnowledgeRepository(db)
    jobs = await repo.get_crawl_jobs(org.id)
    return [{"id": j.id, "url": j.url, "status": j.status, "pages_found": j.pages_found,
             "chunks_created": j.chunks_created, "error": j.error,
             "created_at": j.created_at, "completed_at": j.completed_at} for j in jobs]


@knowledge_router.get("/stats")
async def knowledge_stats(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from app.models import KnowledgeChunk, KnowledgeDocument, CrawlJob
    total_chunks = (await db.execute(select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.org_id == org.id))).scalar_one()
    total_docs = (await db.execute(select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.org_id == org.id))).scalar_one()
    last_crawl = await KnowledgeRepository(db).get_latest_crawl(org.id)
    return {"total_chunks": total_chunks, "total_documents": total_docs,
            "last_crawl_status": last_crawl.status if last_crawl else None,
            "last_crawl_at": last_crawl.completed_at if last_crawl else None}


# ── Dashboard ──────────────────────────────────────────────────────────────
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@dashboard_router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    from_date: Optional[str] = None, to_date: Optional[str] = None,
    org=Depends(get_user_org), db: AsyncSession = Depends(get_db),
):
    from_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else None
    to_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else None
    repo = LeadRepository(db)
    metrics = await repo.get_dashboard_metrics(org.id, from_dt, to_dt)
    return DashboardMetrics(**metrics)


@dashboard_router.get("/ai-feed")
async def get_ai_feed(limit: int = Query(20, le=50), org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = LeadRepository(db)
    return await repo.get_ai_feed(org.id, limit)


@dashboard_router.get("/hot-leads")
async def get_hot_leads(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    r = await db.execute(
        select(Lead).where(Lead.org_id == org.id, Lead.intent_score >= 70,
                           Lead.status.notin_(["meeting_booked", "disqualified", "stopped"]))
        .order_by(Lead.intent_score.desc()).limit(5)
    )
    leads = r.scalars().all()
    return [{"id": l.id, "full_name": l.full_name, "email": l.email, "company": l.company,
             "intent_score": l.intent_score, "status": l.status,
             "recommended_action": l.recommended_action} for l in leads]


# ── Calendar ────────────────────────────────────────────────────────────────
calendar_router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@calendar_router.get("/connect")
async def connect_calendar(org=Depends(get_user_org)):
    return {"auth_url": calendar_service.get_auth_url(org.id)}


@calendar_router.get("/callback")
async def calendar_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import CalendarIntegration
    tokens = calendar_service.exchange_code(code)
    r = await db.execute(select(CalendarIntegration).where(CalendarIntegration.org_id == state))
    integration = r.scalar_one_or_none()
    if integration:
        integration.google_access_token = tokens["access_token"]
        integration.google_refresh_token = tokens["refresh_token"]
        integration.token_expires_at = tokens["token_expires_at"]
    else:
        integration = CalendarIntegration(
            org_id=state, google_access_token=tokens["access_token"],
            google_refresh_token=tokens["refresh_token"],
            token_expires_at=tokens["token_expires_at"],
        )
        db.add(integration)
    await db.flush()
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?calendar=connected")


@calendar_router.get("/status")
async def calendar_status(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import CalendarIntegration
    r = await db.execute(select(CalendarIntegration).where(CalendarIntegration.org_id == org.id))
    return {"connected": r.scalar_one_or_none() is not None}


# ── Public (no auth) ─────────────────────────────────────────────────────────
public_router = APIRouter(prefix="/public", tags=["public"])


@public_router.get("/form/{org_slug}/config")
async def form_config(org_slug: str, db: AsyncSession = Depends(get_db)):
    org = await OrgRepository(db).get_by_slug(org_slug)
    if not org:
        raise NotFoundError("Form not found")
    return {"org_name": org.name, "org_slug": org.slug,
            "fields": [
                {"key": "full_name", "label": "Full Name", "required": True, "type": "text"},
                {"key": "email", "label": "Email", "required": True, "type": "email"},
                {"key": "phone", "label": "Phone", "required": False, "type": "tel"},
                {"key": "company", "label": "Company", "required": False, "type": "text"},
                {"key": "message", "label": "How can we help?", "required": True, "type": "textarea"},
            ]}


@public_router.post("/form/{org_slug}", status_code=201)
@limiter.limit("5/minute")
async def submit_form(
    request: Request, org_slug: str, data: LeadSubmitRequest,
    background_tasks, db: AsyncSession = Depends(get_db),
):
    from fastapi import BackgroundTasks
    org = await OrgRepository(db).get_by_slug(org_slug)
    if not org:
        raise NotFoundError("Form not found")

    ip = request.client.host if request.client else ""
    lead = Lead(org_id=org.id, email=data.email, full_name=data.full_name,
                phone=data.phone, company=data.company, role=data.role,
                message=data.message, custom_fields=data.custom_fields or {},
                utm_source=data.utm_source, utm_medium=data.utm_medium,
                utm_campaign=data.utm_campaign, ip_address=ip, status="new")
    db.add(lead)
    await db.flush()
    await db.refresh(lead)

    conv = Conversation(lead_id=lead.id)
    db.add(conv)
    await db.flush()
    await db.commit()

    background_tasks.add_task(qualify_new_lead, lead.id, org.id, settings.DATABASE_URL)
    return {"lead_id": lead.id, "message": "Thank you! We'll be in touch shortly."}


@public_router.get("/book/{org_slug}")
async def get_slots(org_slug: str, date: str = Query(...), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import CalendarIntegration
    org = await OrgRepository(db).get_by_slug(org_slug)
    if not org:
        raise NotFoundError()
    r = await db.execute(select(CalendarIntegration).where(CalendarIntegration.org_id == org.id))
    integration = r.scalar_one_or_none()
    if not integration:
        raise BadRequestError("Calendar not connected for this business")
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise BadRequestError("Invalid date format. Use YYYY-MM-DD")
    slots = calendar_service.get_available_slots(integration, date_obj)
    return {"slots": slots, "date": date}


@public_router.post("/book/{org_slug}", status_code=201)
@limiter.limit("3/minute")
async def book_slot(
    request: Request, org_slug: str, data: BookSlotRequest,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import CalendarIntegration
    from app.repositories.user_repo import UserRepository

    org = await OrgRepository(db).get_by_slug(org_slug)
    if not org:
        raise NotFoundError()

    lead_repo = LeadRepository(db)
    lead = await lead_repo.get_by_id(data.lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError("Lead not found")

    r = await db.execute(select(CalendarIntegration).where(CalendarIntegration.org_id == org.id))
    integration = r.scalar_one_or_none()
    if not integration:
        raise BadRequestError("Calendar not connected")

    event = calendar_service.create_event(
        integration=integration,
        title=f"Discovery Call: {lead.full_name or lead.email} & {org.name}",
        starts_at=data.starts_at, ends_at=data.ends_at,
        attendee_email=lead.email, attendee_name=lead.full_name or lead.email,
        description=f"Booked via AI Sales Employee.\nOriginal inquiry: {lead.message or 'N/A'}",
    )

    meeting = Meeting(lead_id=lead.id, org_id=org.id,
                      google_event_id=event["event_id"], meet_link=event["meet_link"],
                      starts_at=data.starts_at, ends_at=data.ends_at, status="confirmed")
    db.add(meeting)
    lead.status = "meeting_booked"
    lead.next_action_at = None
    lead.human_takeover = False
    await db.flush()

    starts_str = data.starts_at.strftime("%B %d, %Y at %I:%M %p UTC")
    try:
        await email_service.send_meeting_confirmation(lead.email, lead.full_name or "there", org.name, starts_str, event["meet_link"])
        owner = await UserRepository(db).get_by_id(org.owner_id)
        if owner:
            await email_service.send_owner_meeting_notification(owner.email, lead.full_name or lead.email, lead.email, lead.company or "", starts_str, event["meet_link"])
    except Exception:
        pass

    return {"meeting_id": meeting.id, "meet_link": event["meet_link"],
            "starts_at": data.starts_at.isoformat(), "confirmation": "Meeting confirmed!"}
