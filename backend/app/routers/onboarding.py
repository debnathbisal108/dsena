from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.core.config import settings
from app.models import Organization, CrawlJob, KnowledgeDocument, KnowledgeChunk
from app.repositories.user_repo import OrgRepository
from app.repositories.lead_repo import KnowledgeRepository
from app.schemas import BusinessInfoRequest, AIPolicyRequest, CrawlRequest, OrgOut, CrawlJobOut, AddManualKnowledgeRequest
from app.services.knowledge.crawler import crawl_website, ingest_pdf
from app.services.ai.rag import embed_text

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


async def get_or_require_org(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Organization:
    repo = OrgRepository(db)
    org = await repo.get_by_owner(current_user.id)
    if not org:
        raise NotFoundError("No organization found. Complete step 1 first.")
    return org


@router.post("/business-info", response_model=OrgOut, status_code=201)
async def save_business_info(
    data: BusinessInfoRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = OrgRepository(db)
    existing = await repo.get_by_owner(current_user.id)

    if existing:
        # Update existing
        for field in ["name", "description", "services", "target_customer",
                      "pricing_guidance", "faqs", "business_rules", "website_url"]:
            val = getattr(data, field, None)
            if val is not None:
                setattr(existing, field, val)
        existing.slug = data.slug
        existing.onboarding_step = max(existing.onboarding_step, 2)
        await db.flush()
        await db.refresh(existing)
        return OrgOut.model_validate(existing)

    # Check slug uniqueness
    if await repo.get_by_slug(data.slug):
        raise ConflictError("That URL slug is already taken. Try another.")

    org = Organization(
        owner_id=current_user.id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        services=data.services,
        target_customer=data.target_customer,
        pricing_guidance=data.pricing_guidance,
        faqs=data.faqs,
        business_rules=data.business_rules,
        website_url=data.website_url,
        onboarding_step=2,
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return OrgOut.model_validate(org)


@router.post("/crawl-website", response_model=CrawlJobOut, status_code=201)
async def start_crawl(
    data: CrawlRequest,
    background_tasks: BackgroundTasks,
    org: Organization = Depends(get_or_require_org),
    db: AsyncSession = Depends(get_db),
):
    job = CrawlJob(org_id=org.id, url=data.url, status="pending")
    db.add(job)
    await db.flush()
    await db.refresh(job)

    background_tasks.add_task(crawl_website, org.id, data.url, job.id, settings.DATABASE_URL)
    return CrawlJobOut.model_validate(job)


@router.get("/crawl-status/{job_id}", response_model=CrawlJobOut)
async def crawl_status(
    job_id: str,
    org: Organization = Depends(get_or_require_org),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.org_id == org.id))
    job = r.scalar_one_or_none()
    if not job:
        raise NotFoundError("Crawl job not found")
    return CrawlJobOut.model_validate(job)


@router.post("/upload-document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    org: Organization = Depends(get_or_require_org),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    doc = KnowledgeDocument(
        org_id=org.id,
        filename=file.filename or "upload",
        file_type=file.content_type,
        status="processing",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    if file.content_type == "application/pdf" or (file.filename or "").endswith(".pdf"):
        background_tasks.add_task(ingest_pdf, org.id, doc.id, content, file.filename or "upload", settings.DATABASE_URL)
    else:
        # Plain text
        text = content.decode("utf-8", errors="ignore")
        from app.services.ai.rag import chunk_text
        chunks = chunk_text(text)
        for i, chunk_content in enumerate(chunks):
            embedding = embed_text(chunk_content)
            chunk = KnowledgeChunk(
                org_id=org.id, source_type="pdf",
                title=f"{file.filename} (part {i+1})",
                content=chunk_content, embedding=embedding,
            )
            db.add(chunk)
        doc.status = "done"
        doc.chunks_created = len(chunks)
        await db.flush()

    return {"document_id": doc.id, "filename": doc.filename, "status": doc.status}


@router.post("/add-manual-knowledge")
async def add_manual_knowledge(
    data: AddManualKnowledgeRequest,
    org: Organization = Depends(get_or_require_org),
    db: AsyncSession = Depends(get_db),
):
    embedding = embed_text(data.content)
    chunk = KnowledgeChunk(
        org_id=org.id, source_type="manual",
        title=data.title, content=data.content, embedding=embedding,
    )
    db.add(chunk)
    await db.flush()
    await db.refresh(chunk)
    return {"id": chunk.id, "title": chunk.title}


@router.post("/ai-policy", response_model=OrgOut)
async def save_ai_policy(
    data: AIPolicyRequest,
    org: Organization = Depends(get_or_require_org),
    db: AsyncSession = Depends(get_db),
):
    org.ai_tone = data.ai_tone
    org.max_followup_attempts = data.max_followup_attempts
    org.allowed_hours_start = data.allowed_hours_start
    org.allowed_hours_end = data.allowed_hours_end
    org.allowed_timezone = data.allowed_timezone
    org.onboarding_complete = True
    org.onboarding_step = 5
    await db.flush()
    await db.refresh(org)
    return OrgOut.model_validate(org)


@router.get("/status", response_model=OrgOut)
async def get_onboarding_status(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = OrgRepository(db)
    org = await repo.get_by_owner(current_user.id)
    if not org:
        raise NotFoundError("No organization yet")
    return OrgOut.model_validate(org)
