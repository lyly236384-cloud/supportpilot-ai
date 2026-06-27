from __future__ import annotations

from app.models.schemas import ConversationTurn, Intent

# Multi-turn conversation helpers.
#
# Two responsibilities:
#   1. format_history_for_llm — render recent turns into a compact text block
#      that gets injected into LLM prompts (intent / answer), so the model can
#      resolve references like "那这个呢" / "可以退吗" against earlier turns.
#   2. resolve_followup_intent — a deterministic fallback for the mock engine:
#      when the current message classifies as UNKNOWN but is clearly a short
#      follow-up, inherit the most recent concrete business intent from history.
#      This lets the offline mock demo show coreference handling too.

# Cap how much history we feed the model to bound prompt size / cost.
_MAX_HISTORY_TURNS = 6

# Short follow-ups that lean on prior context rather than restating the topic.
_FOLLOWUP_MARKERS = (
    "那",
    "这个",
    "它",
    "还能",
    "可以吗",
    "怎么弄",
    "怎么办",
    "呢",
    "然后",
    "接着",
    "之后",
    "继续",
)

_BUSINESS_INTENTS = {
    Intent.LOGISTICS_QUESTION,
    Intent.RETURN_REFUND,
    Intent.EXCHANGE_AFTER_SALE,
    Intent.INVOICE_QUESTION,
    Intent.PRODUCT_DAMAGE,
}


def recent_turns(history: list[ConversationTurn] | None) -> list[ConversationTurn]:
    if not history:
        return []
    return history[-_MAX_HISTORY_TURNS:]


def format_history_for_llm(history: list[ConversationTurn] | None) -> str:
    """Render recent turns as a labeled transcript for prompt injection."""
    turns = recent_turns(history)
    if not turns:
        return ""
    lines = []
    for turn in turns:
        speaker = "客户" if turn.role == "user" else "客服"
        lines.append(f"{speaker}：{turn.content}")
    return "\n".join(lines)


def _looks_like_followup(message: str) -> bool:
    text = message.strip()
    # Very short messages, or ones opening with a follow-up marker, lean on context.
    if len(text) <= 8:
        return True
    return any(text.startswith(marker) or marker in text for marker in _FOLLOWUP_MARKERS)


def last_user_intent_keywords(history: list[ConversationTurn] | None) -> str:
    """Concatenate recent user turns so the classifier can re-score with context."""
    turns = recent_turns(history)
    user_text = " ".join(t.content for t in turns if t.role == "user")
    return user_text


def resolve_followup_intent(
    message: str,
    current_intent: Intent,
    history: list[ConversationTurn] | None,
    classify_fn,
) -> tuple[Intent, str] | None:
    """Inherit a prior business intent for short context-dependent follow-ups.

    Returns (intent, reason) when a follow-up should adopt the previous topic,
    or None to keep the current classification. `classify_fn` re-classifies a
    text fragment into an IntentResult (injected to avoid a circular import).
    """
    if current_intent != Intent.UNKNOWN:
        return None
    if not history or not _looks_like_followup(message):
        return None

    # Walk back through user turns to find the most recent concrete intent.
    for turn in reversed(recent_turns(history)):
        if turn.role != "user":
            continue
        prior = classify_fn(turn.content)
        if prior.intent in _BUSINESS_INTENTS:
            return prior.intent, f"承接上文“{turn.content[:20]}”的{prior.intent.value}意图"
    return None
