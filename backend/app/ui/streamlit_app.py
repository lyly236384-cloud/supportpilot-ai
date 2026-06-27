from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/chat"
METRICS_URL = "http://127.0.0.1:8000/api/metrics"
TRACES_URL = "http://127.0.0.1:8000/api/traces"

DEMO_CASES = [
    ("shop_001", "我的快递什么时候发货？"),
    ("shop_002", "订单已经发货了，还能修改收货地址吗？"),
    ("shop_003", "我想退货，七天无理由怎么申请？"),
    ("shop_002", "发票抬头写错了，可以修改吗？"),
    ("shop_001", "收到的杯子碎了，外包装也变形了"),
    ("shop_003", "我要投诉你们并要求赔偿"),
]

ACTION_LABELS = {
    "auto_reply": "AI 自动解决",
    "handoff": "转人工",
    "create_ticket": "创建售后工单",
}

INTENT_LABELS = {
    "logistics_question": "物流配送",
    "return_refund": "退货退款",
    "exchange_after_sale": "换货售后",
    "invoice_question": "发票问题",
    "product_damage": "破损/错发/漏发",
    "complaint_risk": "投诉高风险",
    "unknown": "未知问题",
}

st.set_page_config(page_title="SupportPilot AI 售后运营后台", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; }
    .status-chip {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 999px;
        background: #eef2ff;
        color: #3730a3;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .muted { color: #6b7280; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_json(url: str, fallback):
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return fallback


def run_case(shop_id: str, message: str) -> dict | None:
    try:
        response = requests.post(
            API_URL,
            json={"customer_id": shop_id, "message": message},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"请求后端失败：{exc}")
        st.info("请先启动 FastAPI：uvicorn app.main:app --reload")
        return None


def load_metrics() -> dict:
    return get_json(
        METRICS_URL,
        {
            "total_conversations": 0,
            "auto_reply_count": 0,
            "handoff_count": 0,
            "ticket_count": 0,
            "auto_resolution_rate": 0,
            "handoff_rate": 0,
            "ticket_rate": 0,
            "avg_elapsed_ms": 0,
            "total_estimated_tokens": 0,
        },
    )


def load_traces() -> list[dict]:
    return get_json(TRACES_URL, [])


def build_rows(records: list[dict]) -> list[dict]:
    rows = []
    for record in reversed(records):
        rows.append(
            {
                "trace_id": record.get("trace_id", ""),
                "shop": record.get("customer_id", ""),
                "message": record.get("message", ""),
                "intent": record.get("intent", {}).get("intent", ""),
                "intent_label": INTENT_LABELS.get(record.get("intent", {}).get("intent", ""), "未知问题"),
                "risk": record.get("risk", {}).get("risk_level", ""),
                "action": record.get("action", ""),
                "action_label": ACTION_LABELS.get(record.get("action", ""), record.get("action", "")),
                "elapsed_ms": record.get("elapsed_ms", 0),
                "ticket_id": (record.get("ticket") or {}).get("ticket_id", ""),
                "answer": record.get("answer", ""),
                "citations": record.get("citations", []),
                "raw": record,
            }
        )
    return rows


def seed_demo_data() -> None:
    with st.spinner("正在模拟 C 端消费者咨询..."):
        for shop_id, message in DEMO_CASES:
            run_case(shop_id, message)
    st.rerun()


metrics = load_metrics()
records = load_traces()
rows = build_rows(records)

with st.sidebar:
    st.title("SupportPilot AI")
    st.caption("电商售后客服运营 SaaS MVP")
    page = st.radio(
        "导航",
        ["运营概览", "在线客服队列", "AI 处理记录", "售后工单", "知识库状态", "开发调试"],
    )
    st.divider()
    if st.button("生成一组售后咨询样例", type="primary"):
        seed_demo_data()
    st.caption("样例用于模拟 C 端消费者从外部渠道进入系统。")

st.title(page)

if page == "运营概览":
    st.caption("面向客服经理的服务效率、风险和队列概览。")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("咨询总量", metrics["total_conversations"])
    col2.metric("AI 自动解决率", f"{metrics['auto_resolution_rate']:.0%}")
    col3.metric("转人工量", metrics["handoff_count"])
    col4.metric("售后工单", metrics["ticket_count"])
    col5.metric("平均响应", f"{metrics['avg_elapsed_ms']} ms")

    st.divider()
    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("问题分类分布")
        intent_counts = Counter(row["intent_label"] for row in rows)
        if intent_counts:
            st.bar_chart(pd.DataFrame(intent_counts.items(), columns=["问题类型", "数量"]).set_index("问题类型"))
        else:
            st.info("暂无处理记录。可先生成一组售后咨询样例。")

    with right:
        st.subheader("待人工处理摘要")
        queue_rows = [row for row in rows if row["action"] == "handoff"]
        if queue_rows:
            st.dataframe(
                pd.DataFrame(queue_rows)[["intent_label", "risk", "message", "elapsed_ms"]],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.success("当前没有待人工接管问题。")

    st.subheader("最近处理记录")
    if rows:
        st.dataframe(
            pd.DataFrame(rows[:8])[["action_label", "intent_label", "risk", "message", "elapsed_ms"]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无最近记录。")

elif page == "在线客服队列":
    st.caption("只展示 AI 无法自动解决、需要人工接管的问题。")
    queue_rows = [row for row in rows if row["action"] == "handoff"]
    if not queue_rows:
        st.success("当前没有待人工接管问题。")
    else:
        selected = st.dataframe(
            pd.DataFrame(queue_rows)[["trace_id", "intent_label", "risk", "message", "elapsed_ms"]],
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )
        index = selected.selection.rows[0] if selected.selection.rows else 0
        item = queue_rows[index]
        st.subheader("问题详情")
        st.markdown(f"<span class='status-chip'>{item['intent_label']}</span><span class='status-chip'>{item['risk']}</span>", unsafe_allow_html=True)
        st.write(item["message"])
        st.text_area("AI 摘要 / 建议回复草稿", item["answer"], height=140)
        with st.expander("转人工原因"):
            st.write(item["raw"].get("risk", {}).get("reason", ""))

elif page == "AI 处理记录":
    st.caption("展示已由 AI 自动解决的问题。")
    auto_rows = [row for row in rows if row["action"] == "auto_reply"]
    if auto_rows:
        st.dataframe(
            pd.DataFrame(auto_rows)[["trace_id", "intent_label", "message", "elapsed_ms", "answer"]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无 AI 自动解决记录。")

elif page == "售后工单":
    st.caption("展示商品破损、错发漏发、异常物流等售后工单。")
    ticket_rows = [row for row in rows if row["action"] == "create_ticket"]
    if ticket_rows:
        st.dataframe(
            pd.DataFrame(ticket_rows)[["ticket_id", "intent_label", "risk", "message", "elapsed_ms"]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无售后工单。")

elif page == "知识库状态":
    st.caption("当前 MVP 为只读行业模板，不提供知识库编辑后台。")
    col1, col2, col3 = st.columns(3)
    col1.metric("行业模板", "电商售后")
    col2.metric("文档数量", 8)
    col3.metric("检索模式", "keyword / vector")
    st.subheader("已接入文档")
    st.table(
        pd.DataFrame(
            [
                ["return_policy.md", "退货政策"],
                ["refund_policy.md", "退款规则"],
                ["exchange_policy.md", "换货规则"],
                ["shipping_policy.md", "物流与配送"],
                ["invoice_policy.md", "发票规则"],
                ["damaged_goods_sop.md", "破损处理 SOP"],
                ["complaint_escalation.md", "投诉升级"],
                ["support_reply_guidelines.md", "客服话术"],
            ],
            columns=["文件", "内容"],
        )
    )

else:
    st.caption("开发期调试入口，最终产品版可隐藏或删除。")
    shop_id, message = st.selectbox("选择样例", DEMO_CASES, format_func=lambda item: item[1])
    custom_message = st.text_area("模拟外部渠道消费者问题", message, height=100)
    if st.button("运行工作流", type="primary"):
        result = run_case(shop_id, custom_message)
        if result:
            st.success(ACTION_LABELS.get(result["action"], result["action"]))
            st.write(result["answer"])
            with st.expander("Workflow steps", expanded=True):
                for step in result.get("workflow_steps", []):
                    st.write(f"{step['name']} - {step['summary']}")
                    st.caption(step["detail"])
            with st.expander("RAG citations"):
                st.json(result.get("citations", []))
            with st.expander("Raw JSON"):
                st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")

st.caption(f"最后刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
