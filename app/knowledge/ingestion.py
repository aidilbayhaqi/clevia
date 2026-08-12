from __future__ import annotations

from openai import AsyncOpenAI
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.knowledge.chunking import semantic_chunks


async def _embed_texts(texts: list[str]) -> list[list[float] | None]:
    if not texts:
        return []
    if not settings.KNOWLEDGE_EMBEDDINGS_ENABLED:
        return [None for _ in texts]
    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "KNOWLEDGE_EMBEDDINGS_ENABLED=true requires OPENAI_API_KEY to be configured."
        )
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    result = await client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in result.data]


async def reindex_document(db: AsyncSession, document: KnowledgeDocument) -> list[KnowledgeChunk]:
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
    chunks = semantic_chunks(document.content)
    embeddings = await _embed_texts(chunks)
    rows: list[KnowledgeChunk] = []
    for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        row = KnowledgeChunk(
            clinic_id=document.clinic_id,
            document_id=document.id,
            chunk_index=index,
            content=content,
            metadata_json={
                "title": document.title,
                "source_type": document.source_type,
                "version": document.version,
                "language": document.language,
            },
            embedding=embedding,
        )
        db.add(row)
        rows.append(row)
    await db.flush()
    return rows
