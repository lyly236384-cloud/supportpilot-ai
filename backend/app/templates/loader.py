from __future__ import annotations

import importlib

from app.config.settings import _env
from app.models.schemas import Intent

DEFAULT_TEMPLATE = "demo_ecommerce"


def get_active_template_name() -> str:
    return _env("SUPPORTPILOT_TEMPLATE", DEFAULT_TEMPLATE).lower() or DEFAULT_TEMPLATE


def _load_template():
    name = get_active_template_name()
    try:
        return importlib.import_module(f"app.templates.{name}")
    except ModuleNotFoundError:
        return importlib.import_module(f"app.templates.{DEFAULT_TEMPLATE}")


def get_intent_values_text() -> str:
    return _load_template().INTENT_VALUES


def get_intent_boost_terms() -> dict[Intent, list[str]]:
    return dict(_load_template().INTENT_BOOST_TERMS)


def get_colloquial_expansions() -> list[tuple[str, str]]:
    return list(_load_template().COLLOQUIAL_EXPANSIONS)


def get_domain_terms() -> set[str]:
    return set(_load_template().DOMAIN_TERMS)


def get_query_rewrite_system_prompt() -> str:
    return _load_template().QUERY_REWRITE_SYSTEM_PROMPT


def get_intent_classifier_system_prompt() -> str:
    template = _load_template()
    return f"{template.INTENT_CLASSIFIER_SYSTEM_PROMPT}intent只能是 {template.INTENT_VALUES}。confidence是0到1的小数。reason用一句中文说明。"


def get_risk_controller_system_prompt() -> str:
    return _load_template().RISK_CONTROLLER_SYSTEM_PROMPT


def get_answer_system_prompt() -> str:
    return _load_template().ANSWER_SYSTEM_PROMPT


def get_free_chat_system_prompt() -> str:
    tpl = _load_template()
    if hasattr(tpl, "FREE_CHAT_SYSTEM_PROMPT"):
        return tpl.FREE_CHAT_SYSTEM_PROMPT
    # Fallback for templates that don't define their own FREE_CHAT prompt
    return (
        "你是一个智能 AI 客服代理，名字叫'小P'。你具备深度思考和自主分析能力——"
        "你不是传统的脚本机器人，而是一个能真正理解客户、主动思考的 AI Agent。\n"
        "\n"
        "核心能力：\n"
        "1. 深度理解客户真实需求和潜台词\n"
        "2. 自主推理最佳回复策略，不依赖预设脚本\n"
        "3. 敏锐感知客户情绪，先处理情绪再处理问题\n"
        "4. 信息不足时主动追问，快速定位核心问题\n"
        "5. 拒绝模板化回复，每次对话都是独特的\n"
        "\n"
        "交流原则：\n"
        "- 像资深专家一样思考，而非机器人执行指令\n"
        "- 先理解→再共情→再分析→最后解决\n"
        "- 自然的中文交流，适当使用语气词\n"
        "- 不编造事实，但可给出基于经验的合理建议\n"
        "- 诚实面对不确定性，给出下一步行动建议"
    )


def get_ticket_answer() -> str:
    return _load_template().TICKET_ANSWER


def get_handoff_answer() -> str:
    return _load_template().HANDOFF_ANSWER


def get_insufficient_knowledge_answer() -> str:
    return _load_template().INSUFFICIENT_KNOWLEDGE_ANSWER


def get_ticket_title() -> str:
    return _load_template().TICKET_TITLE


def get_tool_execution_detail() -> str:
    return _load_template().TOOL_EXECUTION_DETAIL
