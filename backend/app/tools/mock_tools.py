from __future__ import annotations

import json
from uuid import uuid4

import requests
from langchain.tools import tool

from app.config import MOCK_DATA_DIR
from app.config.settings import get_feishu_webhook_url, is_feishu_enabled
from app.models.schemas import Ticket

CUSTOMERS_PATH = MOCK_DATA_DIR / "customers.json"

# --- customer data (with file mtime cache for hot-reload) ---

_customer_cache: list[dict] | None = None
_cache_mtime: float = 0.0


def _load_customers() -> list[dict]:
    global _customer_cache, _cache_mtime
    stat = CUSTOMERS_PATH.stat()
    if _customer_cache is not None and stat.st_mtime == _cache_mtime:
        return _customer_cache
    _customer_cache = json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))
    _cache_mtime = stat.st_mtime
    return _customer_cache


def get_customer_profile(customer_id: str) -> dict:
    for customer in _load_customers():
        if customer["customer_id"] == customer_id:
            return customer
    return {
        "customer_id": customer_id,
        "name": f"客户-{customer_id}",
        "plan": "unknown",
        "is_vip": False,
        "contact": "未知联系人",
        "support_owner": "默认客服",
    }


def list_all_customers() -> list[dict]:
    return _load_customers()


# --- ticket creation (local, persisted via trace → SQLite) ---


def create_ticket(customer_id: str, title: str, summary: str, priority: str) -> Ticket:
    customer = get_customer_profile(customer_id)
    return Ticket(
        ticket_id=f"TICKET-{uuid4().hex[:8].upper()}",
        title=title,
        summary=summary,
        priority=priority,
        status="Open",
        assignee=customer.get("support_owner", "默认客服"),
    )


# --- notification: Feishu webhook (real) or mock fallback ---


def _send_feishu_card(ticket: Ticket, customer: dict) -> dict:
    """POST a Feishu card message via webhook."""
    webhook_url = get_feishu_webhook_url()
    priority_color = "red" if ticket.priority == "P0" else "blue"
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"⚠ 服务工单通知 — {ticket.priority}"},
                "template": priority_color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**客户**：{customer.get('name')}\n"
                            f"**工单**：{ticket.ticket_id}\n"
                            f"**标题**：{ticket.title}\n"
                            f"**负责人**：{ticket.assignee}\n"
                            f"**状态**：{ticket.status}"
                        ),
                    },
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"摘要：{ticket.summary[:200]}"}
                    ],
                },
            ],
        },
    }
    resp = requests.post(webhook_url, json=card, timeout=10)
    resp.raise_for_status()
    return {
        "channel": "feishu",
        "sent": True,
        "status_code": resp.status_code,
        "message": f"{customer.get('name')} 创建了 {ticket.priority} 工单 {ticket.ticket_id}，负责人：{ticket.assignee}",
    }


def send_alert(ticket: Ticket, customer: dict) -> dict:
    if is_feishu_enabled():
        try:
            return _send_feishu_card(ticket, customer)
        except Exception as exc:
            return {
                "channel": "feishu_failed",
                "sent": False,
                "error": str(exc),
                "message": (
                    f"{customer.get('name')} 创建了 {ticket.priority} 工单 {ticket.ticket_id}"
                    f"，负责人：{ticket.assignee}（飞书通知发送失败）"
                ),
            }
    return {
        "channel": "mock_feishu",
        "sent": True,
        "message": f"{customer.get('name')} 创建了 {ticket.priority} 工单 {ticket.ticket_id}，负责人：{ticket.assignee}",
    }


# === LangChain tool wrappers (Stage 2) ===


@tool
def get_customer_profile_tool(customer_id: str) -> dict:
    """Retrieve the full customer profile by customer_id.

    Returns plan, VIP status, support owner, and contact info.
    """
    return get_customer_profile(customer_id)


@tool
def create_ticket_tool(customer_id: str, title: str, summary: str, priority: str) -> Ticket:
    """Create a support ticket.

    priority must be 'P0', 'P1', or 'P2'.
    Returns the created Ticket object with ticket_id, status, and assignee.
    """
    return create_ticket(customer_id=customer_id, title=title, summary=summary, priority=priority)


@tool
def send_alert_tool(ticket: Ticket, customer: dict) -> dict:
    """Send notification (Feishu webhook or mock) about a newly created ticket.

    Returns delivery confirmation with channel, sent status, and message.
    """
    return send_alert(ticket, customer)


SUPPORT_TOOLS = [get_customer_profile_tool, create_ticket_tool, send_alert_tool]
