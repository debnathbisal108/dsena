import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import settings

logger = logging.getLogger(__name__)
_scheduler = None


def create_scheduler() -> AsyncIOScheduler:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    scheduler = AsyncIOScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=sync_url, tablename="apscheduler_jobs")}
    )
    scheduler.add_job(
        "app.services.ai.agent:run_agent_loop",
        trigger="interval",
        minutes=settings.AGENT_POLL_INTERVAL_MINUTES,
        id="agent_loop",
        replace_existing=True,
        misfire_grace_time=300,
    )
    return scheduler


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = create_scheduler()
    return _scheduler


def start_scheduler():
    s = get_scheduler()
    if not s.running:
        s.start()
        logger.info("APScheduler started — agent loop every 15 minutes")


def stop_scheduler():
    s = get_scheduler()
    if s.running:
        s.shutdown(wait=False)
