from __future__ import annotations

from app.models.schemas import Action, Citation, IntentResult, MemorySnapshot, RiskResult


def build_memory_snapshot(
    customer_id: str,
    message: str,
    intent: IntentResult,
    risk: RiskResult,
    action: Action,
    citations: list[Citation],
) -> MemorySnapshot:
    """Create a compact, reusable summary for trace review and future memory work."""

    sources = [citation.source for citation in citations[:3]]
    reusable_facts = [
        f"intent={intent.intent.value}",
        f"risk={risk.risk_level.value}",
        f"action={action.value}",
    ]
    if sources:
        reusable_facts.append(f"knowledge_sources={', '.join(sources)}")

    current_summary = (
        f"Customer {customer_id} asked about {intent.intent.value}; "
        f"risk={risk.risk_level.value}; routed_to={action.value}."
    )
    compressed_context = (
        f"message={message[:120]} | "
        f"intent={intent.intent.value} | "
        f"risk={risk.risk_level.value} | "
        f"action={action.value} | "
        f"sources={'; '.join(sources) if sources else 'none'}"
    )

    return MemorySnapshot(
        customer_id=customer_id,
        current_summary=current_summary,
        reusable_facts=reusable_facts,
        compressed_context=compressed_context,
    )
