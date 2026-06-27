import pytest

from app.agent.verifier_agent import verify_answer
from app.models.schemas import Citation, Intent, IntentResult, RiskLevel, RiskResult, VerifierResult


def _citation(source: str, snippet: str) -> Citation:
    return Citation(source=source, snippet=snippet, score=1.0)


def _intent(confidence: float = 0.9) -> IntentResult:
    return IntentResult(intent=Intent.LOGISTICS_QUESTION, confidence=confidence, reason="mock")


def _risk(*, requires_ticket: bool = False, requires_human: bool = False, level: RiskLevel = RiskLevel.LOW) -> RiskResult:
    return RiskResult(
        risk_level=level,
        requires_ticket=requires_ticket,
        requires_human=requires_human,
        reason="mock",
    )


def test_verifier_passes_for_greeting_without_citations():
    result = verify_answer("你好", "您好，我是 SupportPilot AI 客服助手。", [], _risk(), _intent())
    assert result.passed is True
    assert "问候" in result.reason


def test_verifier_rejects_empty_citations_for_non_greeting():
    result = verify_answer(
        "我的快递什么时候发货？",
        "一般 48 小时内发货。",
        [],
        _risk(),
        _intent(),
    )
    assert result.passed is False
    assert "未命中知识库" in result.reason


def test_verifier_skips_ticket_path():
    result = verify_answer(
        "杯子碎了",
        "已创建工单",
        [],
        _risk(requires_ticket=True),
        _intent(),
    )
    assert result.passed is True
    assert "工单" in result.reason


def test_verifier_passes_when_answer_overlaps_citations():
    citations = [
        _citation(
            "shipping_policy.md#发货时效",
            "现货订单支付成功后 48 小时内发货，节假日顺延。",
        )
    ]
    answer = "现货订单支付成功后 48 小时内发货。"
    result = verify_answer("我的快递什么时候发货？", answer, citations, _risk(), _intent())
    assert result.passed is True


def test_verifier_rejects_low_intent_confidence():
    citations = [_citation("shipping_policy.md", "48 小时内发货")]
    result = verify_answer(
        "我的快递什么时候发货？",
        "48 小时内发货",
        citations,
        _risk(),
        _intent(confidence=0.4),
    )
    assert result.passed is False
    assert "置信度" in result.reason
