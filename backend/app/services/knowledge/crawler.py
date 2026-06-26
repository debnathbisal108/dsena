"""
Website crawler. Crawls a URL, extracts text from all pages,
chunks it, embeds it, and stores in knowledge_chunks.
"""
import logging
import asyncio
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import Set
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models import KnowledgeChunk, CrawlJob
from app.services.ai.rag import chunk_text, embed_text

logger = logging.getLogger(__name__)


def _extract_text(html: str) -> str:
    """Extract readable text from HTML using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""


def _get_links(html: str, base_url: str) -> Set[str]:
    """Extract all internal links from a page."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            # Only follow same-domain links, skip anchors/files
            if (parsed.netloc == base_domain and
                not parsed.fragment and
                parsed.scheme in ("http", "https") and
                not any(full_url.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".zip", ".doc"])):
                links.add(full_url.split("?")[0].split("#")[0])
        return links
    except Exception:
        return set()


def _get_page_title(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")
        return title.get_text(strip=True) if title else ""
    except Exception:
        return ""


async def crawl_website(org_id: str, start_url: str, crawl_job_id: str, db_url: str) -> None:
    """
    Full website crawl. Runs as BackgroundTask.
    - Crawls up to MAX_CRAWL_PAGES pages
    - Extracts text from each
    - Chunks + embeds + stores
    """
    engine = create_async_engine(db_url, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        try:
            # Update job status
            from sqlalchemy import select
            job_r = await db.execute(select(CrawlJob).where(CrawlJob.id == crawl_job_id))
            job = job_r.scalar_one_or_none()
            if not job:
                return

            job.status = "running"
            await db.flush()
            await db.commit()

            visited: Set[str] = set()
            to_visit = {start_url}
            pages_processed = 0
            total_chunks = 0
            max_pages = settings.MAX_CRAWL_PAGES

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                while to_visit and pages_processed < max_pages:
                    url = to_visit.pop()
                    if url in visited:
                        continue
                    visited.add(url)

                    try:
                        response = await client.get(
                            url,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; AISalesBot/1.0)"}
                        )
                        if response.status_code != 200:
                            continue
                        content_type = response.headers.get("content-type", "")
                        if "text/html" not in content_type:
                            continue

                        html = response.text
                        text = _extract_text(html)
                        title = _get_page_title(html)

                        if len(text) < 100:
                            continue

                        # Get more links to crawl
                        new_links = _get_links(html, url)
                        to_visit.update(new_links - visited)

                        # Chunk the page
                        chunks = chunk_text(text, chunk_size=400, overlap=50)
                        for i, chunk_content in enumerate(chunks):
                            embedding = embed_text(chunk_content)
                            chunk = KnowledgeChunk(
                                org_id=org_id,
                                source_type="website",
                                source_url=url,
                                title=f"{title} (part {i+1})" if title else f"Page: {url}",
                                content=chunk_content,
                                embedding=embedding,
                            )
                            db.add(chunk)
                            total_chunks += 1

                        pages_processed += 1
                        await db.flush()

                        # Small delay to be respectful
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        logger.warning(f"Failed to crawl {url}: {e}")
                        continue

            # Mark job complete
            async with Session() as db2:
                job_r2 = await db2.execute(select(CrawlJob).where(CrawlJob.id == crawl_job_id))
                job2 = job_r2.scalar_one_or_none()
                if job2:
                    job2.status = "done"
                    job2.pages_found = pages_processed
                    job2.chunks_created = total_chunks
                    job2.completed_at = datetime.now(timezone.utc)
                await db2.commit()

            await db.commit()
            logger.info(f"Crawl complete: {pages_processed} pages, {total_chunks} chunks for org {org_id}")

        except Exception as e:
            logger.error(f"Crawl failed for org {org_id}: {e}")
            async with Session() as db3:
                from sqlalchemy import select as sel
                job_r3 = await db3.execute(sel(CrawlJob).where(CrawlJob.id == crawl_job_id))
                job3 = job_r3.scalar_one_or_none()
                if job3:
                    job3.status = "failed"
                    job3.error = str(e)
                await db3.commit()
        finally:
            await engine.dispose()


async def ingest_pdf(org_id: str, doc_id: str, file_content: bytes, filename: str, db_url: str) -> None:
    """Extract text from PDF and store as knowledge chunks."""
    engine = create_async_engine(db_url, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        try:
            from sqlalchemy import select
            from app.models import KnowledgeDocument

            doc_r = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
            doc = doc_r.scalar_one_or_none()
            if not doc:
                return

            # Extract text from PDF
            try:
                import PyPDF2
                import io
                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text() + "\n"
            except Exception as e:
                doc.status = "failed"
                doc.error = f"PDF extraction failed: {e}"
                await db.commit()
                return

            if not full_text.strip():
                doc.status = "failed"
                doc.error = "No text found in PDF"
                await db.commit()
                return

            chunks = chunk_text(full_text, chunk_size=400, overlap=50)
            for i, chunk_content in enumerate(chunks):
                embedding = embed_text(chunk_content)
                chunk = KnowledgeChunk(
                    org_id=org_id,
                    source_type="pdf",
                    title=f"{filename} (part {i+1})",
                    content=chunk_content,
                    embedding=embedding,
                )
                db.add(chunk)

            doc.status = "done"
            doc.chunks_created = len(chunks)
            await db.commit()
            logger.info(f"PDF ingested: {filename}, {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            await engine.dispose()
