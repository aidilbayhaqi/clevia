from __future__ import annotations

import re
import uuid
from datetime import date

from openai import AsyncOpenAI
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.enums import KnowledgeStatus
from app.db.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.knowledge.schemas import RetrievedKnowledge


SOURCE_PRIORITY = {
    "operational_policy": 0,
    "service_catalog": 1,
    "operational_faq": 2,
    "general_supporting": 3,
}


def _tokens(query: str) -> list[str]:
    return [token for token in re.findall(r"[\w-]+", query.lower()) if len(token) >= 3][:8]


def _source_ref(document: KnowledgeDocument, chunk: KnowledgeChunk) -> str:
    return f"kb:{document.id}:v{document.version}:chunk:{chunk.chunk_index}"


class RetrievalService:
    async def _query_embedding(self, query: str) -> list[float] | None:
        if not settings.KNOWLEDGE_EMBEDDINGS_ENABLED or not settings.OPENAI_API_KEY:
            return None
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=[query],
        )
        return response.data[0].embedding

    async def search(
        self,
        db: AsyncSession,
        *,
        clinic_id: uuid.UUID,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedKnowledge]:
        today = date.today()
        base_filters = (
            KnowledgeDocument.clinic_id == clinic_id,
            KnowledgeDocument.status == KnowledgeStatus.APPROVED,
            or_(KnowledgeDocument.valid_from.is_(None), KnowledgeDocument.valid_from <= today),
            or_(KnowledgeDocument.valid_until.is_(None), KnowledgeDocument.valid_until >= today),
            KnowledgeChunk.clinic_id == clinic_id,
        )

        candidates: dict[uuid.UUID, tuple[KnowledgeDocument, KnowledgeChunk, float]] = {}
        words = _tokens(query)
        keyword_conditions = []
        for word in words:
            like = f"%{word}%"
            keyword_conditions.extend(
                [
                    KnowledgeChunk.content.ilike(like),
                    KnowledgeDocument.title.ilike(like),
                    KnowledgeDocument.category.ilike(like),
                ]
            )

        if keyword_conditions:
            keyword_query = (
                select(KnowledgeDocument, KnowledgeChunk)
                .join(KnowledgeChunk, KnowledgeChunk.document_id == KnowledgeDocument.id)
                .where(and_(*base_filters), or_(*keyword_conditions))
            )
            keyword_rows = (
                await db.execute(keyword_query.limit(max(limit * 4, 12)))
            ).all()
            for rank, (document, chunk) in enumerate(keyword_rows):
                score = 1.0 - min(rank, 20) * 0.02
                candidates[chunk.id] = (document, chunk, score)

        query_embedding = await self._query_embedding(query)
        if query_embedding is not None:
            distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
            vector_query = (
                select(KnowledgeDocument, KnowledgeChunk, distance.label("distance"))
                .join(KnowledgeChunk, KnowledgeChunk.document_id == KnowledgeDocument.id)
                .where(and_(*base_filters), KnowledgeChunk.embedding.is_not(None))
                .order_by(distance)
                .limit(max(limit * 4, 12))
            )
            vector_rows = (await db.execute(vector_query)).all()
            for document, chunk, vector_distance in vector_rows:
                vector_score = max(0.0, 1.0 - float(vector_distance or 1.0))
                existing = candidates.get(chunk.id)
                if existing:
                    candidates[chunk.id] = (
                        document,
                        chunk,
                        max(existing[2], vector_score),
                    )
                else:
                    candidates[chunk.id] = (document, chunk, vector_score)

        ranked = sorted(
            candidates.values(),
            key=lambda row: (
                SOURCE_PRIORITY.get(row[0].source_type, 99),
                -row[2],
                -row[0].version,
                row[1].chunk_index,
            ),
        )
        return [
            RetrievedKnowledge(
                source_ref=_source_ref(document, chunk),
                document_id=str(document.id),
                title=document.title,
                source_type=document.source_type,
                version=document.version,
                content=chunk.content,
                score=round(score, 4),
            )
            for document, chunk, score in ranked[:limit]
        ]


retrieval_service = RetrievalService()
