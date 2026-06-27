from __future__ import annotations

from app.models.schemas import Intent
from app.templates.loader import get_colloquial_expansions, get_intent_boost_terms

# Default demo_ecommerce fallback values live in app.templates.demo_ecommerce.


def rewrite_query_for_retrieval(query: str, intent: Intent | None = None) -> str:
    """Rule-based rewrite with optional LLM enrichment when configured."""
    rewritten = rewrite_query(query, intent)

    from app.config.settings import is_llm_query_rewrite_enabled
    from app.services.llm_client import is_deepseek_enabled, rewrite_search_query_with_llm

    if not is_llm_query_rewrite_enabled() or not is_deepseek_enabled():
        return rewritten

    try:
        llm_terms = rewrite_search_query_with_llm(query, intent)
        return _join_unique_terms([rewritten, llm_terms])
    except Exception:
        return rewritten


def rewrite_query(query: str, intent: Intent | None = None) -> str:
    """Expand colloquial customer wording into retrieval-friendly search terms."""
    normalized = query.strip()
    if not normalized:
        return normalized

    terms: list[str] = [normalized]

    for phrase, expansion in get_colloquial_expansions():
        if phrase in normalized:
            terms.append(expansion)

    if intent is not None:
        terms.extend(get_intent_boost_terms().get(intent, []))

    return _join_unique_terms(terms)


def _join_unique_terms(parts: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []

    for part in parts:
        for token in part.split():
            key = token.lower()
            if key in seen or _is_redundant_token(token, ordered):
                continue
            seen.add(key)
            ordered.append(token)

    return " ".join(ordered)


def _is_redundant_token(token: str, existing: list[str]) -> bool:
    for item in existing:
        if token in item or item in token:
            return True
    return False
