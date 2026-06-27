from __future__ import annotations

import json
import os
from contextvars import ContextVar
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.models.schemas import Citation, Intent, IntentResult, RiskLevel, RiskResult
from app.templates.loader import (
    get_answer_system_prompt,
    get_free_chat_system_prompt,
    get_intent_classifier_system_prompt,
    get_query_rewrite_system_prompt,
    get_risk_controller_system_prompt,
)

load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
INTENT_VALUES = "logistics_question、return_refund、exchange_after_sale、invoice_question、product_damage、complaint_risk、unknown"
_LLM_TOKEN_USAGE: ContextVar[int] = ContextVar("llm_token_usage", default=0)


def reset_llm_token_usage() -> None:
    _LLM_TOKEN_USAGE.set(0)


def get_llm_token_usage() -> int:
    return _LLM_TOKEN_USAGE.get()


def _extract_total_tokens(message: Any) -> int:
    usage_metadata = getattr(message, "usage_metadata", None) or {}
    total = usage_metadata.get("total_tokens") or usage_metadata.get("total")
    if total is not None:
        return int(total)

    response_metadata = getattr(message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    total = token_usage.get("total_tokens") or token_usage.get("total")
    if total is not None:
        return int(total)

    raw_usage = getattr(message, "usage", None)
    if isinstance(raw_usage, dict):
        total = raw_usage.get("total_tokens") or raw_usage.get("total")
        if total is not None:
            return int(total)
    return 0


def _record_llm_usage(message: Any) -> None:
    total_tokens = _extract_total_tokens(message)
    if total_tokens > 0:
        _LLM_TOKEN_USAGE.set(_LLM_TOKEN_USAGE.get() + total_tokens)


def record_llm_response_usage(message: Any) -> None:
    _record_llm_usage(message)


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


def _invoke_llm_with_usage(prompt: ChatPromptTemplate, llm: ChatOpenAI, payload: dict) -> Any:
    response = llm.invoke(prompt.format_messages(**payload))
    _record_llm_usage(response)
    return response


def _parsed_structured_result(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    _record_llm_usage(result.get("raw"))
    parsed = result.get("parsed")
    if parsed is None:
        raise ValueError(f"structured output parsing failed: {result.get('parsing_error')}")
    return parsed


# ============================================================
#  Provider configuration (pluggable LLM backend)
# ============================================================

_PROVIDER_CONFIGS: dict[str, dict[str, str]] = {
    "deepseek": {
        "model_env": "DEEPSEEK_MODEL",
        "model_default": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "model_env": "OPENAI_MODEL",
        "model_default": "gpt-4o-mini",
        "base_url_env": "OPENAI_BASE_URL",
        "base_url_default": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "qwen": {
        "model_env": "QWEN_MODEL",
        "model_default": "qwen-plus",
        "base_url_env": "QWEN_BASE_URL",
        "base_url_default": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "QWEN_API_KEY",
    },
}


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "mock").strip().lower()


def _deepseek_api_key() -> str:
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


def resolve_llm_config() -> dict:
    """Return {provider, model, base_url, api_key} for the active LLM_PROVIDER.

    Returns {"provider": "mock"} when no real provider is configured.
    """
    provider = _provider()
    cfg = _PROVIDER_CONFIGS.get(provider)
    if cfg is None:
        return {"provider": "mock"}

    model = os.getenv(cfg.get("model_env", ""), cfg.get("model_default", "")).strip()
    api_key = os.getenv(cfg.get("api_key_env", ""), "").strip()

    base_url: str
    if "base_url_env" in cfg:
        base_url = os.getenv(cfg["base_url_env"], cfg["base_url_default"]).strip()
    else:
        base_url = cfg["base_url"]

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
    }


def resolve_free_chat_config() -> dict:
    """Like resolve_llm_config() but allows a different model for free chat.

    Set FREE_CHAT_MODEL env var to override the model used for free-chat only
    (e.g. FREE_CHAT_MODEL=deepseek-reasoner for deep thinking).
    """
    base = resolve_llm_config()
    if base.get("provider") == "mock":
        return base
    free_model = os.getenv("FREE_CHAT_MODEL", "").strip()
    if free_model:
        base = dict(base)
        base["model"] = free_model
    return base


def get_chat_openai_for_free_chat(temperature: float = 0.7) -> ChatOpenAI | None:
    """Factory returning ChatOpenAI for free-chat (may use a different model).

    Returns None when provider is 'mock' or no API key is configured.
    """
    config = resolve_free_chat_config()
    if config.get("provider") == "mock" or not config.get("api_key"):
        return None
    return ChatOpenAI(
        model=config["model"],
        base_url=config["base_url"],
        api_key=config["api_key"],
        temperature=temperature,
        max_retries=2,
        timeout=60,  # longer timeout for reasoning models
    )


def is_llm_enabled() -> bool:
    """True when a real LLM provider is configured with a non-empty API key."""
    config = resolve_llm_config()
    return config.get("provider") != "mock" and bool(config.get("api_key"))


def is_deepseek_enabled() -> bool:
    """Backward-compatible alias; prefer is_llm_enabled() for new code."""
    return is_llm_enabled()


def rewrite_search_query_with_llm(query: str, intent: Intent | None = None) -> str:
    intent_hint = intent.value if intent is not None else "unknown"
    content = _call_deepseek(
        [
            {
                "role": "system",
                "content": (
                    get_query_rewrite_system_prompt(),
                ),
            },
            {"role": "user", "content": f"意图：{intent_hint}\n用户问题：{query}"},
        ],
        temperature=0,
    )
    return content.strip()


def _call_deepseek(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    """Provider-agnostic LLM call (kept as backward-compatible alias)."""
    return _call_llm(messages, temperature)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removesuffix("```").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in LLM output: {text}")
    return json.loads(cleaned[start : end + 1])


# ============================================================
#  LangChain ChatOpenAI factory (provider-agnostic)
# ============================================================


def get_chat_openai(temperature: float = 0.0) -> ChatOpenAI | None:
    """Factory returning ChatOpenAI for the active LLM_PROVIDER.

    Returns None when provider is 'mock' or no API key is configured.
    """
    config = resolve_llm_config()
    if config.get("provider") == "mock" or not config.get("api_key"):
        return None
    return ChatOpenAI(
        model=config["model"],
        base_url=config["base_url"],
        api_key=config["api_key"],
        temperature=temperature,
        max_retries=2,
        timeout=30,
    )


def _call_llm(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
) -> str:
    """Call LLM via ChatOpenAI + LCEL (provider-agnostic)."""
    config = resolve_llm_config()
    if config.get("provider") == "mock":
        raise RuntimeError("LLM is not configured (mock mode)")
    llm = get_chat_openai(temperature=temperature)
    if llm is None:
        raise RuntimeError("LLM is not configured — provider or API key missing")
    prompt = ChatPromptTemplate.from_messages(
        [(msg["role"], msg["content"]) for msg in messages]
    )
    response = _invoke_llm_with_usage(prompt, llm, {})
    return _message_text(response)


# -----------------------------------------------------------
#  Structured-output variants (replaces raw JSON parsing)
# -----------------------------------------------------------


def classify_intent_with_structured_output(message: str, history=None) -> IntentResult:
    """Intent classification via LangChain structured output (function calling).

    Falls back to the direct DeepSeek JSON call when the OpenAI-compatible
    endpoint does not support LangChain structured-output response formats.
    """
    if is_greeting_message(message):
        return IntentResult(intent=Intent.UNKNOWN, confidence=0.92, reason="问候语")
    if not is_deepseek_enabled():
        return classify_intent_with_history(message, history, _base=mock_classify_intent)

    from app.memory.conversation import format_history_for_llm

    history_block = format_history_for_llm(history)
    human_template = (
        "对话上文：\n{history}\n\n当前客户问题：{message}"
        if history_block
        else "客户问题：{message}"
    )
    try:
        llm = get_chat_openai(temperature=0.0)
        structured_llm = llm.with_structured_output(
            IntentResult,
            method="json_mode",
            include_raw=True,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    get_intent_classifier_system_prompt(),
                ),
                ("human", human_template),
            ]
        )
        chain = prompt | structured_llm
        payload = {"message": message}
        if history_block:
            payload["history"] = history_block
        return _parsed_structured_result(chain.invoke(payload))
    except Exception:
        return classify_intent_with_llm(message, history)


def risk_check_with_structured_output(
    intent_result: IntentResult, message: str
) -> RiskResult:
    """Risk assessment via LangChain structured output.

    High-risk cases always go through the deterministic rule gate first.
    Falls back to the direct DeepSeek JSON call when the OpenAI-compatible
    endpoint does not support LangChain structured-output response formats.
    """
    # 高风险动作继续优先用确定性规则兜底，避免模型误放行。
    rule_result = mock_risk_check(intent_result, message)
    if rule_result.risk_level == RiskLevel.HIGH:
        return rule_result

    if not is_deepseek_enabled():
        return rule_result

    try:
        llm = get_chat_openai(temperature=0.0)
        structured_llm = llm.with_structured_output(
            RiskResult,
            method="json_mode",
            include_raw=True,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    get_risk_controller_system_prompt(),
                ),
                (
                    "human",
                    "客户问题：{message}\n意图：{intent}\n意图置信度：{confidence}",
                ),
            ]
        )
        chain = prompt | structured_llm
        result = chain.invoke(
            {
                "message": message,
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
            }
        )
        return _parsed_structured_result(result)
    except Exception:
        return risk_check_with_llm(intent_result, message)


# -----------------------------------------------------------
#  LangChain answer generator (LCEL chain)
# -----------------------------------------------------------


def generate_answer_with_langchain(
    message: str, intent: Intent, citations: list[Citation], history=None
) -> str:
    """Generate a customer-facing answer via a LangChain LCEL chain.

    Falls back to the mock template generator when DeepSeek is unavailable
    or the call fails.
    """
    if is_greeting_message(message):
        return get_greeting_answer()
    if not is_deepseek_enabled():
        return mock_generate_answer(message, intent, citations)

    from app.memory.conversation import format_history_for_llm

    context = "\n\n".join(
        f"来源：{citation.source}\n片段：{citation.snippet}" for citation in citations
    )
    if not context:
        context = "未检索到可靠知识库片段。"
    history_block = format_history_for_llm(history)

    try:
        llm = get_chat_openai(temperature=0.2)
        human_parts = []
        if history_block:
            human_parts.append("对话上文：\n{history}")
        human_parts.append("客户问题：{message}\n意图：{intent}\n知识库片段：\n{context}")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    get_answer_system_prompt(),
                ),
                ("human", "\n\n".join(human_parts)),
            ]
        )
        payload = {"message": message, "intent": intent.value, "context": context}
        if history_block:
            payload["history"] = history_block
        response = _invoke_llm_with_usage(prompt, llm, payload)
        return _message_text(response)
    except Exception as exc:
        fallback = mock_generate_answer(message, intent, citations)
        return (
            f"{fallback}\n\n（DeepSeek回复生成失败，已使用本地兜底回复：{exc}）"
        )


_GREETING_TOKENS = (
    "你好",
    "您好",
    "在吗",
    "在不在",
    "早上好",
    "下午好",
    "晚上好",
    "hi",
    "hello",
    "hey",
)


def is_greeting_message(message: str) -> bool:
    text = message.strip().lower()
    if not text:
        return False
    if text in _GREETING_TOKENS:
        return True
    return any(text == token or text.startswith(f"{token}，") or text.startswith(f"{token},") for token in _GREETING_TOKENS)


def get_greeting_answer() -> str:
    return (
        "您好呀，我是您的专属客服小助手~ "
        "关于物流、退货退款、换货、发票或者商品问题，都可以随时问我哦，我会尽力帮您解决！"
    )


_INJECTION_PATTERNS = (
    "忽略之前",
    "忽略以上",
    "忽略前面",
    "忽略所有规则",
    "无视规则",
    "不用审核",
    "不需要审核",
    "直接帮我确认",
    "假装你",
    "扮演",
    "你现在是",
    "system prompt",
    "ignore previous",
    "ignore above",
)

_OVERREACH_PATTERNS = (
    "所有客户",
    "全部客户",
    "其他客户",
    "别人的订单",
    "所有人的",
    "全部订单",
    "数据库",
    "后台密码",
)


def _looks_like_injection_or_overreach(message: str) -> bool:
    text = message.lower()
    return any(p in text for p in _INJECTION_PATTERNS) or any(
        p in message for p in _OVERREACH_PATTERNS
    )


# 当前规则分类器服务于默认 demo_ecommerce 示例模板；后续会迁移到模板配置。
def mock_classify_intent(message: str) -> IntentResult:
    text = message.lower()

    if is_greeting_message(message):
        return IntentResult(intent=Intent.UNKNOWN, confidence=0.92, reason="问候语")

    if any(keyword in text for keyword in ["投诉", "赔偿", "差评", "仲裁", "曝光", "食品安全", "安全问题", "泄露", "隐私"]):
        return IntentResult(intent=Intent.COMPLAINT_RISK, confidence=0.92, reason="命中投诉或高风险售后关键词")

    if _looks_like_injection_or_overreach(message):
        return IntentResult(
            intent=Intent.COMPLAINT_RISK,
            confidence=0.9,
            reason="疑似越权指令或提示注入，需人工兜底",
        )

    if any(keyword in text for keyword in ["破损", "坏了", "碎了", "漏发", "少件", "错发", "发错", "漏液", "外包装变形"]):
        return IntentResult(intent=Intent.PRODUCT_DAMAGE, confidence=0.9, reason="命中商品破损、错发或漏发关键词")

    if any(keyword in text for keyword in ["退款", "退货", "仅退款", "退钱", "退回", "退费"]):
        return IntentResult(intent=Intent.RETURN_REFUND, confidence=0.9, reason="命中退货或退款关键词")

    if any(keyword in text for keyword in ["换货", "换一件", "尺码不合适", "颜色选错", "补发"]):
        return IntentResult(intent=Intent.EXCHANGE_AFTER_SALE, confidence=0.88, reason="命中换货或售后处理关键词")

    if any(keyword in text for keyword in ["发票", "开票", "抬头", "税号"]):
        return IntentResult(intent=Intent.INVOICE_QUESTION, confidence=0.88, reason="命中发票相关关键词")

    if any(keyword in text for keyword in ["物流", "快递", "发货", "配送", "签收", "没收到", "地址", "改地址", "派送", "停滞"]):
        return IntentResult(intent=Intent.LOGISTICS_QUESTION, confidence=0.88, reason="命中物流或配送关键词")

    return IntentResult(intent=Intent.UNKNOWN, confidence=0.45, reason="未命中明确意图，需谨慎处理")


def classify_intent_with_llm(message: str, history=None) -> IntentResult:
    # Greetings are a deterministic rule, not an LLM judgment — keep this
    # symmetric with mock_classify_intent so downstream risk/action are stable.
    if is_greeting_message(message):
        return IntentResult(intent=Intent.UNKNOWN, confidence=0.92, reason="问候语")
    if not is_deepseek_enabled():
        return classify_intent_with_history(message, history, _base=mock_classify_intent)

    from app.memory.conversation import format_history_for_llm

    history_block = format_history_for_llm(history)
    user_content = (
        f"对话上文：\n{history_block}\n\n当前客户问题：{message}"
        if history_block
        else f"客户问题：{message}"
    )
    try:
        content = _call_deepseek(
            [
                {
                    "role": "system",
                    "content": (
                        "你是 SupportPilot AI 客服运营平台的意图分类器，当前使用 demo_ecommerce 示例意图集。只输出JSON，不要输出解释。"
                        f"intent只能是 {INTENT_VALUES}。"
                        "如果当前问题是承接上文的追问（如“那这个呢”“可以退吗”），请结合对话上文判断意图。"
                        "confidence是0到1的小数。reason用一句中文说明。"
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )
        data = _extract_json(content)
        return IntentResult(
            intent=Intent(data.get("intent", "unknown")),
            confidence=float(data.get("confidence", 0.5)),
            reason=str(data.get("reason", "DeepSeek结构化分类结果")),
        )
    except Exception as exc:
        fallback = classify_intent_with_history(message, history, _base=mock_classify_intent)
        fallback.reason = f"DeepSeek分类失败，已回退规则分类：{exc}；{fallback.reason}"
        return fallback


def classify_intent_with_history(message, history=None, *, _base=None) -> IntentResult:
    """Rule-based classification augmented with coreference resolution.

    Used by the mock engine: when the current message alone is UNKNOWN but it's
    a short follow-up, inherit the most recent business intent from history.
    """
    classify = _base or mock_classify_intent
    result = classify(message)
    if not history:
        return result

    from app.memory.conversation import resolve_followup_intent

    resolved = resolve_followup_intent(message, result.intent, history, classify)
    if resolved is not None:
        intent, reason = resolved
        return IntentResult(intent=intent, confidence=0.7, reason=reason)
    return result


# 当前风险规则服务于默认 demo_ecommerce 示例模板；后续会迁移到模板配置。
def mock_risk_check(intent_result: IntentResult, message: str) -> RiskResult:
    text = message.lower()

    # Greetings carry no risk and should be answered, not escalated. This must
    # be deterministic across engines (the LLM may otherwise assign low
    # confidence to "你好"/"在吗" and trip the handoff path).
    if is_greeting_message(message):
        return RiskResult(
            risk_level=RiskLevel.LOW,
            requires_human=False,
            requires_ticket=False,
            reason="问候语，无风险",
        )

    if intent_result.intent == Intent.COMPLAINT_RISK:
        return RiskResult(
            risk_level=RiskLevel.HIGH,
            requires_human=True,
            requires_ticket=False,
            reason="涉及投诉、赔偿、商品安全或敏感风险，必须人工兜底",
        )

    if intent_result.intent == Intent.RETURN_REFUND and any(keyword in text for keyword in ["大额", "赔偿", "投诉", "必须", "立刻", "平台介入"]):
        return RiskResult(
            risk_level=RiskLevel.HIGH,
            requires_human=True,
            requires_ticket=False,
            reason="退款诉求包含高风险表达，需要人工审核",
        )

    if intent_result.intent == Intent.PRODUCT_DAMAGE or (
        intent_result.intent == Intent.LOGISTICS_QUESTION
        and any(keyword in text for keyword in ["超过72小时", "72小时", "丢失", "破损", "没收到", "签收但"])
    ):
        return RiskResult(
            risk_level=RiskLevel.HIGH,
            requires_human=False,
            requires_ticket=True,
            reason="疑似交付异常或履约异常，需要创建服务工单",
        )

    if intent_result.confidence < 0.6:
        return RiskResult(
            risk_level=RiskLevel.MEDIUM,
            requires_human=True,
            requires_ticket=False,
            reason="意图置信度较低，转人工确认",
        )

    return RiskResult(
        risk_level=RiskLevel.LOW,
        requires_human=False,
        requires_ticket=False,
        reason="普通售后咨询，可尝试自动回复",
    )


def risk_check_with_llm(intent_result: IntentResult, message: str) -> RiskResult:
    # 高风险动作继续优先用确定性规则兜底，避免模型误放行。
    rule_result = mock_risk_check(intent_result, message)
    if rule_result.risk_level == RiskLevel.HIGH:
        return rule_result

    if not is_deepseek_enabled():
        return rule_result

    try:
        content = _call_deepseek(
            [
                {
                    "role": "system",
                    "content": (
                        "你是 SupportPilot AI 客服运营平台的风险控制器，当前使用 demo_ecommerce 示例风险规则。只输出JSON，不要输出解释。"
                        "risk_level只能是 low、medium、high。requires_human和requires_ticket是布尔值。"
                        "投诉、赔偿、隐私、安全、大额退款等高风险请求必须requires_human=true。需要持续跟进或履约异常的问题应requires_ticket=true。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"客户问题：{message}\n意图：{intent_result.intent}\n意图置信度：{intent_result.confidence}",
                },
            ],
            temperature=0,
        )
        data = _extract_json(content)
        return RiskResult(
            risk_level=RiskLevel(data.get("risk_level", rule_result.risk_level)),
            requires_human=bool(data.get("requires_human", rule_result.requires_human)),
            requires_ticket=bool(data.get("requires_ticket", rule_result.requires_ticket)),
            reason=str(data.get("reason", "DeepSeek风险判断结果")),
        )
    except Exception as exc:
        rule_result.reason = f"DeepSeek风险判断失败，已回退规则判断：{exc}；{rule_result.reason}"
        return rule_result


def _clean_snippet(snippet: str) -> str:
    return snippet.replace("## ", "").strip().rstrip("。")


def _build_answer_from_citations(message: str, citations: list[Citation]) -> str:
    snippets = []
    seen = set()

    for citation in citations:
        snippet = _clean_snippet(citation.snippet)
        if snippet and snippet not in seen:
            snippets.append(snippet)
            seen.add(snippet)

    is_comparison = any(keyword in message for keyword in ["区别", "对比", "不同", "差异"])
    if is_comparison and len(snippets) > 1:
        points = "\n".join(f"- {snippet}" for snippet in snippets[:3])
        return f"您好，我帮您梳理了一下：\n{points}\n希望能帮到您~"

    if len(snippets) >= 2:
        combined = "。".join(snippets[:3])
        return f"您好，{combined}。希望能帮到您~"

    return f"您好，{snippets[0]}。希望能帮到您~"


def mock_generate_answer(message: str, intent: Intent, citations: list[Citation]) -> str:
    if is_greeting_message(message):
        return get_greeting_answer()

    if intent == Intent.COMPLAINT_RISK:
        return (
            "非常理解您的心情，您反馈的问题确实让人着急。"
            "我已经帮您把情况记录下来并转接给人工客服专员了，他们会尽快核实并跟进处理，请您放心~"
        )

    if intent == Intent.PRODUCT_DAMAGE:
        return (
            "哎呀，遇到这种情况确实挺糟心的，非常抱歉给您带来了不好的体验。"
            "我已经帮您创建了服务工单，后续会有专员跟进核实，"
            "也麻烦您补充一下相关的凭证和问题发生的具体时间，这样我们可以更快帮您处理~"
        )

    if not citations:
        return (
            "很抱歉，目前我暂时没有查到足够的信息来确认这个问题。"
            "为了避免给您带来误导，我建议帮您转接人工客服进一步确认，您看可以吗？"
        )

    return _build_answer_from_citations(message, citations)


def generate_answer(message: str, intent: Intent, citations: list[Citation]) -> str:
    if is_greeting_message(message):
        return get_greeting_answer()
    if not is_deepseek_enabled():
        return mock_generate_answer(message, intent, citations)

    context = "\n\n".join(
        f"来源：{citation.source}\n片段：{citation.snippet}" for citation in citations
    )
    if not context:
        context = "未检索到可靠知识库片段。"

    try:
        return _call_deepseek(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个温暖、专业的电商客服助手。请以真人客服的口吻与客户交流。"
                        "先共情再解决：理解客户的问题和情绪，用自然亲和的语言给出解答。"
                        "严禁使用'根据知识库资料'、'参考来源'等机械表述，直接自然地回答即可。"
                        "投诉/赔偿/大额退款/隐私/安全 → 用安抚语气说明已转人工，不承诺具体结果。"
                        "需要持续跟进 → 说明已创建工单并安抚客户。"
                        "知识库无依据 → 坦诚说明，温和引导转人工。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"客户问题：{message}\n意图：{intent}\n知识库片段：\n{context}",
                },
            ],
            temperature=0.3,
        )
    except Exception as exc:
        fallback = mock_generate_answer(message, intent, citations)
        return f"{fallback}\n\n（DeepSeek回复生成失败，已使用本地兜底回复：{exc}）"


PRODUCT_CHAT_SYSTEM_PROMPT = (
    "你是 SupportPilot AI 官网产品助手，只负责介绍产品本身，不处理具体客户订单或售后案例。"
    "请用简洁中文回答，通常 2-4 句话。"
    "你可以介绍：企业客服运营平台定位、AI 分流、知识库、转人工、服务工单、数据概览、适用行业和 MVP 试用方式。"
    "不要编造未上线能力，例如真实语音机器人、完整多租户 SaaS、已商用定价。"
    "如果问题超出产品介绍范围，礼貌说明当前助手只介绍产品能力，并引导用户进入工作台体验或继续询问产品相关问题。"
)


def generate_product_chat_answer(message: str) -> str:
    if not is_deepseek_enabled():
        raise RuntimeError("DeepSeek is not configured for product chat")

    return _call_deepseek(
        [
            {"role": "system", "content": PRODUCT_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.3,
    )


# ============================================================
#  Free-chat mode (LLM autonomous dialogue without RAG)
# ============================================================

# FREE_CHAT_SYSTEM_PROMPT is now loaded from the active template.
# Kept as a module-level getter for convenience; callers should prefer
# get_free_chat_system_prompt() for fresh values after template switches.
FREE_CHAT_SYSTEM_PROMPT = get_free_chat_system_prompt()


THINKING_SYSTEM_PROMPT = (
    "你是一个 AI 客服代理的「思考模块」。你的任务是快速分析客户消息，"
    "输出一句简短的中文分析（不超过50字），涵盖："
    "1) 客户真正的意图或潜台词是什么；"
    "2) 客户当前的情绪状态；"
    "3) 最佳的应对策略。"
    "只输出分析，不要输出回答或建议。"
)


def _think_about_query(message: str, history=None) -> str:
    """快速分析客户消息的真实意图、情绪和最佳策略。

    返回简短的中文分析文本，用于驱动后续的回复生成。
    当 LLM 不可用时返回空字符串。
    """
    if not is_llm_enabled():
        return ""

    from app.memory.conversation import format_history_for_llm

    history_block = format_history_for_llm(history)
    user_content = (
        f"对话历史：\n{history_block}\n\n当前客户消息：{message}"
        if history_block
        else f"客户消息：{message}"
    )

    try:
        return _call_llm(
            [
                {"role": "system", "content": THINKING_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )
    except Exception:
        return ""


def generate_free_chat_answer(message: str, history=None) -> str:
    """自由对话模式：LLM 自主回答，不强制依赖知识库引用。

    先分析客户意图和情绪，再生成个性化回复。
    保留安全护栏：问候语快速通道、提示注入检测。
    当 LLM 不可用时回退到问候语兜底。
    """
    if is_greeting_message(message):
        return get_greeting_answer()

    if _looks_like_injection_or_overreach(message):
        return "您的问题需要人工客服进一步处理。我们已记录诉求，并会尽快安排专员跟进。"

    if not is_llm_enabled():
        return get_greeting_answer()

    from app.memory.conversation import format_history_for_llm

    # Phase 1: Think — analyze the query
    thinking = _think_about_query(message, history)

    # Phase 2: Answer — generate personalized response
    history_block = format_history_for_llm(history)
    user_content_parts = []
    if history_block:
        user_content_parts.append(f"对话历史：\n{history_block}")
    if thinking:
        user_content_parts.append(f"内部思考分析：{thinking}")
    user_content_parts.append(f"客户当前消息：{message}\n请基于以上分析，用自然亲和的语言回复客户。")
    user_content = "\n\n".join(user_content_parts)

    try:
        return _call_llm(
            [
                {"role": "system", "content": FREE_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
        )
    except Exception as exc:
        return (
            f"{get_greeting_answer()}\n"
            f"（自由对话生成失败，已使用本地兜底回复）"
        )


async def stream_free_chat_answer(message: str, history=None):
    """自由对话流式生成器：先思考分析，再逐 token 生成回复。

    两阶段流式：
    - Phase 1: yield ("thinking", 思考内容) — 展示 AI 的分析过程
    - Phase 2: yield ("token", 回复token) — 逐字展示最终回复

    当 LLM 不可用时 yield 兜底消息。
    """
    if is_greeting_message(message):
        yield ("token", get_greeting_answer())
        return

    if _looks_like_injection_or_overreach(message):
        yield ("token", "您的问题需要人工客服进一步处理。我们已记录诉求。")
        return

    config = resolve_free_chat_config()
    if config.get("provider") == "mock":
        yield ("token", get_greeting_answer())
        return

    # Use deepseek-reasoner for native CoT if configured; otherwise our own thinking step
    is_reasoner = "reasoner" in config.get("model", "").lower()
    llm = get_chat_openai_for_free_chat(temperature=0.7)
    if llm is None:
        yield ("token", get_greeting_answer())
        return

    from app.memory.conversation import format_history_for_llm

    history_block = format_history_for_llm(history)

    # ---- Phase 1: Thinking ----
    # When using a reasoner model (e.g. deepseek-reasoner), the model natively
    # outputs chain-of-thought. We skip our own thinking step to avoid redundancy.
    thinking = ""
    if not is_reasoner:
        thinking = _think_about_query(message, history)
        if thinking:
            yield ("thinking", thinking)

    # ---- Phase 2: Answer ----
    user_content_parts = []
    if history_block:
        user_content_parts.append(f"对话历史：\n{history_block}")
    if thinking:
        user_content_parts.append(f"内部思考分析：{thinking}")
    user_content_parts.append(f"客户当前消息：{message}\n请基于以上分析，用自然亲和的语言回复客户。")
    user_content = "\n\n".join(user_content_parts)

    prompt = ChatPromptTemplate.from_messages([
        ("system", FREE_CHAT_SYSTEM_PROMPT),
        ("user", user_content),
    ])
    chain = prompt | llm
    try:
        async for chunk in chain.astream({}):
            _record_llm_usage(chunk)
            # reasoner models may emit reasoning_content before content
            if hasattr(chunk, "reasoning_content") and chunk.reasoning_content:
                yield ("thinking", chunk.reasoning_content)
            if hasattr(chunk, "content") and chunk.content:
                yield ("token", chunk.content)
    except Exception:
        yield ("token", get_greeting_answer())
