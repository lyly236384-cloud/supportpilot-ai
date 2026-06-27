from __future__ import annotations

from app.models.schemas import Citation
from app.rag.base import BaseRetriever
from app.rag.dense_retriever import get_dense_retriever
from app.rag.keyword_retriever import KeywordRetriever
from app.rag.vector_retriever import VectorRetriever


class HybridRetriever(BaseRetriever):
    """Hybrid retrieval fusing lexical (keyword) and semantic (dense) signals.

    The semantic side prefers a real embedding retriever (bge + FAISS) and falls
    back to the dependency-free token-vector retriever when the ML stack is not
    available, so hybrid search degrades gracefully instead of failing.
    """

    def __init__(self) -> None:
        self.keyword = KeywordRetriever()
        self.semantic: BaseRetriever = get_dense_retriever() or VectorRetriever()

    def retrieve(self, query: str, top_k: int = 3) -> list[Citation]:
        keyword_hits = self.keyword.retrieve(query=query, top_k=top_k * 2)
        semantic_hits = self.semantic.retrieve(query=query, top_k=top_k * 2)

        merged: dict[str, Citation] = {}
        scores: dict[str, float] = {}

        for rank, citation in enumerate(keyword_hits, start=1):
            key = citation.source
            merged[key] = citation
            scores[key] = scores.get(key, 0) + self._weighted_score(
                citation.score, rank, weight=0.6
            )

        for rank, citation in enumerate(semantic_hits, start=1):
            key = citation.source
            merged.setdefault(key, citation)
            scores[key] = scores.get(key, 0) + self._weighted_score(
                citation.score, rank, weight=0.4
            )

        reranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [
            Citation(
                source=merged[source].source,
                snippet=merged[source].snippet,
                score=round(score, 3),
            )
            for source, score in reranked[:top_k]
        ]

    def _weighted_score(self, score: float, rank: int, weight: float) -> float:
        reciprocal_rank = 1 / max(rank, 1)
        return (score * 0.75 + reciprocal_rank * 0.25) * weight
