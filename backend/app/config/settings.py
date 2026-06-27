from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_rag_retriever() -> str:
    return _env("RAG_RETRIEVER", "hybrid").lower()


def get_rag_top_k() -> int:
    raw = _env("RAG_TOP_K", "5")
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def get_rag_min_score() -> float:
    raw = _env("RAG_MIN_SCORE", "0.12")
    try:
        return float(raw)
    except ValueError:
        return 0.12


def get_rag_keyword_min_score() -> float:
    raw = _env("RAG_KEYWORD_MIN_SCORE", "2.0")
    try:
        return float(raw)
    except ValueError:
        return 2.0


def get_rag_dense_min_score() -> float:
    """Absolute cosine-similarity floor for dense retrieval.

    Embeddings return a best match for any query, so an absolute threshold is
    needed to reject semantically unrelated chunks (e.g. greetings) that lexical
    retrievers naturally filter out by returning nothing. bge-small-zh has a high
    similarity baseline (~0.39 even for off-topic text), while genuine matches
    score ~0.5-0.82, so 0.45 cleanly separates the two.
    """
    raw = _env("RAG_DENSE_MIN_SCORE", "0.45")
    try:
        return float(raw)
    except ValueError:
        return 0.45


def get_workflow_engine() -> str:
    return _env("LLM_WORKFLOW_ENGINE", "procedural").lower()


def use_langgraph_engine() -> bool:
    return get_workflow_engine() == "langgraph"


def is_query_rewrite_enabled() -> bool:
    return _env("RAG_QUERY_REWRITE", "true").lower() in {"1", "true", "yes", "on"}


def get_storage_backend() -> str:
    return _env("STORAGE_BACKEND", "sqlite").lower()


def is_llm_query_rewrite_enabled() -> bool:
    return _env("RAG_QUERY_REWRITE_LLM", "false").lower() in {"1", "true", "yes", "on"}


def use_sqlite_storage() -> bool:
    return get_storage_backend() == "sqlite"


def get_feishu_webhook_url() -> str:
    raw = _env("FEISHU_WEBHOOK_URL", "mock").strip()
    if raw.lower() in {"", "mock", "none", "false", "0"}:
        return ""
    return raw


def is_feishu_enabled() -> bool:
    return bool(get_feishu_webhook_url())


def is_auto_seed_enabled() -> bool:
    return _env("AUTO_SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes", "on"}
