from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from app.models import Lead, Conversation, Message, KnowledgeChunk, KnowledgeDocument, CrawlJob, AIAction


class LeadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str) -> Optional[Lead]:
        r = await self.db.execute(select(Lead).where(Lead.id == id))
        return r.scalar_one_or_none()

    async def get_with_details(self, lead_id: str) -> Optional[Lead]:
        r = await self.db.execute(
            select(Lead)
            .options(
                selectinload(Lead.conversation).selectinload(Conversation.messages),
                selectinload(Lead.ai_actions),
                selectinload(Lead.meetings),
            )
            .where(Lead.id == lead_id)
        )
        return r.scalar_one_or_none()

    async def list_by_org(
        self, org_id: str, page: int = 1, limit: int = 25,
        status: Optional[str] = None, search: Optional[str] = None,
        needs_human: bool = False,
    ) -> Tuple[List[Lead], int]:
        q = select(Lead).where(Lead.org_id == org_id)
        cq = select(func.count()).select_from(Lead).where(Lead.org_id == org_id)

        if status:
            q = q.where(Lead.status == status)
            cq = cq.where(Lead.status == status)
        if needs_human:
            q = q.where(Lead.human_takeover == True)
            cq = cq.where(Lead.human_takeover == True)
        if search:
            like = f"%{search}%"
            from sqlalchemy import or_
            f = or_(Lead.email.ilike(like), Lead.full_name.ilike(like), Lead.company.ilike(like))
            q = q.where(f)
            cq = cq.where(f)

        total = (await self.db.execute(cq)).scalar_one()
        q = q.order_by(Lead.intent_score.desc(), Lead.created_at.desc()).offset((page - 1) * limit).limit(limit)
        leads = list((await self.db.execute(q)).scalars().all())
        return leads, total

    async def get_due_for_agent(self) -> List[Lead]:
        """Leads where AI should evaluate next action."""
        now = datetime.now(timezone.utc)
        r = await self.db.execute(
            select(Lead)
            .options(
                selectinload(Lead.conversation).selectinload(Conversation.messages),
                selectinload(Lead.organization),
                selectinload(Lead.ai_actions),
            )
            .where(
                and_(
                    Lead.next_action_at <= now,
                    Lead.human_takeover == False,
                    Lead.status.notin_(["meeting_booked", "disqualified", "unsubscribed", "stopped"]),
                )
            )
        )
        return list(r.scalars().all())

    async def get_dashboard_metrics(self, org_id: str, from_dt: Optional[datetime], to_dt: Optional[datetime]) -> dict:
        base = Lead.org_id == org_id
        if from_dt:
            base = and_(base, Lead.created_at >= from_dt)
        if to_dt:
            base = and_(base, Lead.created_at <= to_dt)

        total = (await self.db.execute(select(func.count()).select_from(Lead).where(base))).scalar_one()
        contacted = (await self.db.execute(select(func.count()).select_from(Lead).where(and_(base, Lead.status != "new")))).scalar_one()
        booked = (await self.db.execute(select(func.count()).select_from(Lead).where(and_(base, Lead.status == "meeting_booked")))).scalar_one()
        hot = (await self.db.execute(select(func.count()).select_from(Lead).where(and_(base, Lead.intent_score >= 70)))).scalar_one()
        needs_human = (await self.db.execute(select(func.count()).select_from(Lead).where(and_(base, Lead.human_takeover == True)))).scalar_one()

        pipeline_r = await self.db.execute(select(func.sum(Lead.estimated_deal_value)).where(and_(base, Lead.estimated_deal_value.isnot(None))))
        pipeline = float(pipeline_r.scalar_one() or 0)

        ai_count = (await self.db.execute(
            select(func.count()).select_from(AIAction).where(AIAction.org_id == org_id)
        )).scalar_one()

        followup_count = (await self.db.execute(
            select(func.count()).select_from(AIAction).where(
                and_(AIAction.org_id == org_id, AIAction.action_type == "followup")
            )
        )).scalar_one()

        by_day_r = await self.db.execute(
            select(cast(Lead.created_at, Date).label("date"), func.count().label("count"))
            .where(base).group_by(cast(Lead.created_at, Date)).order_by(cast(Lead.created_at, Date))
        )
        leads_by_day = [{"date": str(r[0]), "count": r[1]} for r in by_day_r]

        return {
            "leads_received": total,
            "leads_contacted": contacted,
            "meetings_booked": booked,
            "pipeline_value": pipeline,
            "conversion_rate": round(booked / total * 100, 2) if total else 0.0,
            "ai_actions_taken": ai_count,
            "followups_sent": followup_count,
            "hot_leads": hot,
            "leads_needing_human": needs_human,
            "avg_response_time_minutes": 1.2,  # TODO: compute from first message delta
            "leads_by_day": leads_by_day,
            "score_distribution": {"high": hot, "medium": max(0, contacted - hot), "low": max(0, total - contacted)},
        }

    async def get_ai_feed(self, org_id: str, limit: int = 20) -> List[dict]:
        r = await self.db.execute(
            select(AIAction, Lead.full_name, Lead.email)
            .join(Lead, Lead.id == AIAction.lead_id)
            .where(AIAction.org_id == org_id)
            .order_by(AIAction.created_at.desc())
            .limit(limit)
        )
        rows = r.all()
        return [
            {
                "id": row[0].id,
                "lead_name": row[1] or row[2],
                "action_type": row[0].action_type,
                "reasoning": row[0].reasoning,
                "created_at": row[0].created_at,
            }
            for row in rows
        ]


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_chunks_by_org(self, org_id: str) -> List[KnowledgeChunk]:
        r = await self.db.execute(select(KnowledgeChunk).where(KnowledgeChunk.org_id == org_id).order_by(KnowledgeChunk.created_at.desc()))
        return list(r.scalars().all())

    async def get_all_chunks_with_embeddings(self, org_id: str) -> List[KnowledgeChunk]:
        r = await self.db.execute(
            select(KnowledgeChunk)
            .where(and_(KnowledgeChunk.org_id == org_id, KnowledgeChunk.embedding.isnot(None)))
        )
        return list(r.scalars().all())

    async def delete_chunk(self, chunk_id: str) -> None:
        r = await self.db.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id))
        chunk = r.scalar_one_or_none()
        if chunk:
            await self.db.delete(chunk)
            await self.db.flush()

    async def get_documents(self, org_id: str) -> List[KnowledgeDocument]:
        r = await self.db.execute(select(KnowledgeDocument).where(KnowledgeDocument.org_id == org_id).order_by(KnowledgeDocument.created_at.desc()))
        return list(r.scalars().all())

    async def get_crawl_jobs(self, org_id: str) -> List[CrawlJob]:
        r = await self.db.execute(select(CrawlJob).where(CrawlJob.org_id == org_id).order_by(CrawlJob.created_at.desc()))
        return list(r.scalars().all())

    async def get_latest_crawl(self, org_id: str) -> Optional[CrawlJob]:
        r = await self.db.execute(
            select(CrawlJob).where(CrawlJob.org_id == org_id).order_by(CrawlJob.created_at.desc()).limit(1)
        )
        return r.scalar_one_or_none()
