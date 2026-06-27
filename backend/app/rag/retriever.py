from __future__ import annotations

from app.config.settings import (
    get_rag_keyword_min_score,
    get_rag_min_score,
    get_rag_retriever,
    get_rag_top_k,
    is_query_rewrite_enabled,
)
from app.models.schemas import Citation, Intent
from app.rag.base import BaseRetriever
from app.rag.dense_retriever import get_dense_retriever
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.keyword_retriever import KeywordRetriever
from app.rag.query_rewriter import rewrite_query_for_retrieval
from app.rag.vector_retriever import VectorRetriever


def _build_dense_retriever() -> BaseRetriever:
    """Real embedding retriever, falling back to lexical vectors when unavailable."""
    dense = get_dense_retriever()
    if dense is not None:
        return dense
    return VectorRetriever()


RETRIEVERS: dict[str, type[BaseRetriever]] = {
    "hybrid": HybridRetriever,
    "keyword": KeywordRetriever,
    "vector": VectorRetriever,
}

# Factories produce a retriever instance; used for strategies whose concrete
# implementation is resolved at runtime (e.g. dense with graceful fallback).
RETRIEVER_FACTORIES: dict[str, "callable[[], BaseRetriever]"] = {
    "dense": _build_dense_retriever,
}


def get_retriever() -> BaseRetriever:
    strategy = get_rag_retriever()
    factory = RETRIEVER_FACTORIES.get(strategy)
    if factory is not None:
        return factory()
    retriever_class = RETRIEVERS.get(strategy)
    if retriever_class is None:
        available = "、".join(sorted({*RETRIEVERS, *RETRIEVER_FACTORIES}))
        raise ValueError(f"Unsupported RAG_RETRIEVER={strategy}. Available retrievers: {available}")
    return retriever_class()


def retrieve_knowledge(
    query: str,
    top_k: int | None = None,
    *,
    intent: Intent | None = None,
) -> list[Citation]:
    strategy = get_rag_retriever()
    limit = top_k or get_rag_top_k()
    search_query = _build_search_query(query, intent)
    citations = get_retriever().retrieve(query=search_query, top_k=limit)
    return _apply_min_score(citations, strategy)


def _build_search_query(query: str, intent: Intent | None) -> str:
    if not is_query_rewrite_enabled():
        return query
    return rewrite_query_for_retrieval(query, intent)


def _apply_min_score(citations: list[Citation], strategy: str) -> list[Citation]:
    if not citations:
        return []

    best_score = max(citation.score for citation in citations)
    threshold = get_rag_keyword_min_score() if strategy == "keyword" else get_rag_min_score()
    if best_score < threshold:
        return []
    return citations
