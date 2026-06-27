from __future__ import annotations

import re

from app.models.schemas import Citation, IntentResult, RiskLevel, RiskResult, VerifierResult
from app.services.llm_client import is_greeting_message


def verify_answer(
    message: str,
    answer: str,
    citations: list[Citation],
    risk: RiskResult,
    intent: IntentResult,
    *,
    is_free_chat: bool = False,
) -> VerifierResult:
    if risk.requires_ticket:
        return VerifierResult(passed=True, reason="工单路径，跳过自动回复校验")

    if risk.requires_human or risk.risk_level == RiskLevel.HIGH:
        return VerifierResult(passed=True, reason="人工接管路径，跳过自动回复校验")

    if is_greeting_message(message):
        return VerifierResult(passed=True, reason="问候语，无需知识库引用")

    # Free-chat mode: skip citation-based checks, only validate basic safety.
    if is_free_chat:
        if not answer.strip():
            return VerifierResult(passed=False, reason="自由对话答复为空")
        return VerifierResult(passed=True, reason="自由对话路径，已通过安全护栏")

    if not citations:
        return VerifierResult(passed=False, reason="未命中知识库引用，禁止自动回复")

    if not answer.strip():
        return VerifierResult(passed=False, reason="答复为空")

    if intent.confidence < 0.6:
        return VerifierResult(passed=False, reason=f"意图置信度过低 ({intent.confidence:.2f})")

    if not _answer_supported_by_citations(answer, citations):
        return VerifierResult(passed=False, reason="答复内容未能被知识库片段充分支撑")

    return VerifierResult(passed=True, reason="答复与知识库引用一致")


def _answer_supported_by_citations(answer: str, citations: list[Citation]) -> bool:
    answer_tokens = _extract_tokens(answer)
    if not answer_tokens:
        return False

    citation_tokens: set[str] = set()
    for citation in citations:
        citation_tokens.update(_extract_tokens(citation.snippet))
        citation_tokens.update(_extract_tokens(citation.source))

    overlap = answer_tokens & citation_tokens
    if len(overlap) >= 2:
        return True

    # Allow short policy answers when at least one substantive token overlaps.
    substantive = {token for token in overlap if len(token) >= 2}
    return len(substantive) >= 1 and len(citation_tokens) >= 3


def _extract_tokens(text: str) -> set[str]:
    normalized = text.lower()
    latin = set(re.findall(r"[a-z0-9_]{2,}", normalized))
    cjk = set(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    return latin | cjk
