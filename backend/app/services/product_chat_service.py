from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services import llm_client

_logger = logging.getLogger(__name__)

PRODUCT_FAQ = [
    {
        "keywords": ["行业", "适合", "场景", "谁用", "哪些企业"],
        "answer": (
            "SupportPilot AI 适用于需要统一承接客户咨询、AI 分流、人工协同和知识库管理的企业服务场景，"
            "例如电商零售、教育咨询、本地服务、企业服务和生活消费等行业。"
        ),
    },
    {
        "keywords": ["知识库", "资料", "文档", "政策"],
        "answer": (
            "平台支持把企业服务政策、常见问题、SOP 和话术统一放进知识库，"
            "让 AI 和人工客服基于同一套可信内容回复客户。"
        ),
    },
    {
        "keywords": ["转人工", "人工", "协同", "接管"],
        "answer": (
            "当问题风险较高、证据不足或需要人工判断时，系统会把上下文、摘要和建议动作一起转给人工队列，"
            "避免复杂问题被错误自动处理。"
        ),
    },
    {
        "keywords": ["工单", "跟进", "ticket"],
        "answer": (
            "对于需要结构化跟进的问题，系统可以自动创建服务工单，"
            "并在工作台中持续跟踪状态、负责人和处理备注。"
        ),
    },
    {
        "keywords": ["数据", "指标", "概览", "分析", "运营"],
        "answer": (
            "工作台提供数据概览，展示咨询总量、AI 自动处理量、转人工数量、工单量和风险问题，"
            "帮助管理者复盘客服运营效率。"
        ),
    },
    {
        "keywords": ["语音", "电话", "外呼"],
        "answer": (
            "语音 AI 属于后续扩展能力。当前 MVP 先在官网说明应用价值，"
            "暂不承诺真实语音通话、ASR/TTS 或呼叫中心集成。"
        ),
    },
    {
        "keywords": ["价格", "收费", "试用", "部署"],
        "answer": (
            "当前版本是 MVP 演示系统，可通过「免费试用」进入工作台体验核心闭环。"
            "正式商业化定价、部署方式和私有化方案可在后续产品化阶段补充。"
        ),
    },
]

DEFAULT_ANSWER = (
    "SupportPilot AI 是企业客服运营平台，核心能力包括 AI 问题识别、知识库检索、"
    "自动回复、人工队列、服务工单和数据概览。你可以继续问我：适合哪些行业、"
    "知识库怎么用、如何转人工、是否支持工单和数据复盘。"
)


@dataclass(frozen=True)
class ProductChatResult:
    answer: str
    source: str


def _answer_with_faq(message: str) -> str:
    for item in PRODUCT_FAQ:
        if any(keyword in message for keyword in item["keywords"]):
            return item["answer"]
    return DEFAULT_ANSWER


def answer_product_question(message: str) -> ProductChatResult:
    text = message.strip()
    if not text:
        return ProductChatResult(answer=DEFAULT_ANSWER, source="default")

    if llm_client.is_deepseek_enabled():
        try:
            llm_answer = llm_client.generate_product_chat_answer(text).strip()
            if llm_answer:
                return ProductChatResult(answer=llm_answer, source="llm")
        except Exception:
            _logger.warning("DeepSeek product chat failed, falling back to FAQ", exc_info=True)

    faq_answer = _answer_with_faq(text)
    if faq_answer != DEFAULT_ANSWER:
        return ProductChatResult(answer=faq_answer, source="faq")

    return ProductChatResult(answer=DEFAULT_ANSWER, source="default")
