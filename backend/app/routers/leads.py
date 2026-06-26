from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import math
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.repositories.lead_repo import LeadRepository
from app.repositories.user_repo import OrgRepository
from app.schemas import LeadDetail, LeadListItem, PaginatedLeads

router = APIRouter(prefix="/api/leads", tags=["leads"])


async def get_user_org(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = await OrgRepository(db).get_by_owner(current_user.id)
    if not org:
        raise ForbiddenError("No organization found")
    return org


@router.get("", response_model=PaginatedLeads)
async def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    needs_human: bool = False,
    org=Depends(get_user_org),
    db: AsyncSession = Depends(get_db),
):
    repo = LeadRepository(db)
    leads, total = await repo.list_by_org(org.id, page, limit, status, search, needs_human)
    return PaginatedLeads(
        items=[LeadListItem.model_validate(l) for l in leads],
        total=total, page=page,
        pages=math.ceil(total / limit) if total else 1,
    )


@router.get("/hot", response_model=PaginatedLeads)
async def hot_leads(org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = LeadRepository(db)
    from sqlalchemy import select
    from app.models import Lead
    r = await db.execute(
        select(Lead)
        .where(Lead.org_id == org.id, Lead.intent_score >= 70,
               Lead.status.notin_(["meeting_booked", "disqualified", "stopped"]))
        .order_by(Lead.intent_score.desc()).limit(10)
    )
    leads = list(r.scalars().all())
    return PaginatedLeads(items=[LeadListItem.model_validate(l) for l in leads],
                          total=len(leads), page=1, pages=1)


@router.get("/{lead_id}", response_model=LeadDetail)
async def get_lead(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = LeadRepository(db)
    lead = await repo.get_with_details(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError("Lead not found")
    return LeadDetail.model_validate(lead)


@router.post("/{lead_id}/human-takeover")
async def human_takeover(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError()
    lead.human_takeover = True
    lead.status = "needs_human"
    lead.next_action_at = None
    await db.flush()
    return {"message": "Lead handed over to human. AI will not send further messages."}


@router.post("/{lead_id}/release-to-ai")
async def release_to_ai(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta, timezone
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError()
    lead.human_takeover = False
    lead.status = "ai_contacted"
    lead.next_action_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()
    return {"message": "Lead returned to AI agent."}


@router.post("/{lead_id}/disqualify")
async def disqualify(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError()
    lead.status = "disqualified"
    lead.next_action_at = None
    lead.human_takeover = False
    await db.flush()
    return {"message": "Lead disqualified."}


@router.post("/{lead_id}/force-followup")
async def force_followup(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    """Trigger immediate AI evaluation for this lead."""
    from datetime import datetime, timezone
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError()
    lead.next_action_at = datetime.now(timezone.utc)
    lead.human_takeover = False
    await db.flush()
    return {"message": "AI evaluation scheduled immediately."}


@router.get("/{lead_id}/ai-actions")
async def get_ai_actions(lead_id: str, org=Depends(get_user_org), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import AIAction
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead or lead.org_id != org.id:
        raise NotFoundError()
    r = await db.execute(select(AIAction).where(AIAction.lead_id == lead_id).order_by(AIAction.created_at.desc()))
    actions = r.scalars().all()
    return [{"id": a.id, "action_type": a.action_type, "reasoning": a.reasoning,
             "response_content": a.response_content, "tokens_used": a.tokens_used,
             "created_at": a.created_at} for a in actions]
