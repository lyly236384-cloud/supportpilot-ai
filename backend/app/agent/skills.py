from __future__ import annotations

from app.models.schemas import Action, IntentResult, RiskResult, SkillCall


def build_skill_calls(
    intent: IntentResult,
    risk: RiskResult,
    citations_count: int,
    action: Action,
    ticket_created: bool,
) -> list[SkillCall]:
    """Record the deterministic skill route used by the support agent."""

    calls = [
        SkillCall(
            name="intent_router",
            purpose="Classify the customer request and choose the service lane.",
            status="completed",
            input_summary="customer_message",
            output_summary=f"intent={intent.intent.value}, confidence={intent.confidence:.2f}",
        ),
        SkillCall(
            name="risk_guard",
            purpose="Detect complaints, compensation requests, abnormal logistics, and ticket-worthy cases.",
            status="completed",
            input_summary=f"intent={intent.intent.value}",
            output_summary=(
                f"risk={risk.risk_level.value}, human={risk.requires_human}, "
                f"ticket={risk.requires_ticket}"
            ),
        ),
        SkillCall(
            name="knowledge_retrieval",
            purpose="Retrieve grounded knowledge before generating a reply.",
            status="completed" if citations_count else "warning",
            input_summary="customer_message",
            output_summary=f"citations={citations_count}",
        ),
        SkillCall(
            name="action_policy",
            purpose="Route the case to auto reply, human queue, or service ticket.",
            status="completed",
            input_summary=f"risk={risk.risk_level.value}, citations={citations_count}",
            output_summary=f"action={action.value}",
        ),
    ]

    calls.append(
        SkillCall(
            name="ticket_tool",
            purpose="Create a service ticket when structured follow-up is required.",
            status="completed" if ticket_created else "skipped",
            input_summary=f"action={action.value}",
            output_summary="ticket_created" if ticket_created else "not_required",
        )
    )
    return calls

