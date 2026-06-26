"""
RAG (Retrieval Augmented Generation) service.
Embeds text using sentence-transformers (free, local).
Stores embeddings as JSON arrays in PostgreSQL.
Retrieves top-k most similar chunks for any query.
"""
import logging
import json
import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import KnowledgeChunk
from app.repositories.lead_repo import KnowledgeRepository

logger = logging.getLogger(__name__)

# Lazy-loaded embedding model — only loads on first use
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _model = None
    return _model


def embed_text(text: str) -> Optional[List[float]]:
    model = get_embedding_model()
    if not model:
        return None
    try:
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def retrieve_relevant_context(
    query: str,
    org_id: str,
    db: AsyncSession,
    top_k: int = 5,
    min_similarity: float = 0.3,
) -> str:
    """
    Embed the query, find the most similar knowledge chunks,
    return them as a formatted string for injection into prompts.
    """
    try:
        query_embedding = embed_text(query)
        if not query_embedding:
            return await _get_fallback_context(org_id, db)

        repo = KnowledgeRepository(db)
        chunks = await repo.get_all_chunks_with_embeddings(org_id)

        if not chunks:
            return await _get_fallback_context(org_id, db)

        # Score all chunks
        scored = []
        for chunk in chunks:
            if chunk.embedding:
                sim = cosine_similarity(query_embedding, chunk.embedding)
                if sim >= min_similarity:
                    scored.append((sim, chunk))

        # Sort by similarity descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        if not top:
            return await _get_fallback_context(org_id, db)

        parts = []
        for sim, chunk in top:
            title = f"[{chunk.title}] " if chunk.title else ""
            parts.append(f"{title}{chunk.content}")

        return "\n\n---\n\n".join(parts)

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return ""


async def _get_fallback_context(org_id: str, db: AsyncSession) -> str:
    """If no embeddings yet, return first 3 chunks as plain text."""
    try:
        repo = KnowledgeRepository(db)
        chunks = await repo.get_chunks_by_org(org_id)
        if not chunks:
            return ""
        return "\n\n".join(c.content for c in chunks[:3])
    except Exception:
        return ""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]
