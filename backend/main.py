from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.middleware.rate_limit import limiter, rate_limit_handler
from app.routers.auth import router as auth_router
from app.routers.onboarding import router as onboarding_router
from app.routers.leads import router as leads_router
from app.routers.other_routers import (
    knowledge_router, dashboard_router, calendar_router, public_router
)
from app.services.scheduler_service import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="AI Sales Employee API",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(leads_router)
app.include_router(knowledge_router)
app.include_router(dashboard_router)
app.include_router(calendar_router)
app.include_router(public_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "environment": settings.ENVIRONMENT}
