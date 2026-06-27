import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _parse_sse_data_events(response_text: str) -> list[dict]:
    events = []
    for line in response_text.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line.removeprefix("data:").strip()))
    return events


def test_product_chat_returns_answer_without_writing_trace(monkeypatch, tmp_path: Path):
    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)

    client = TestClient(app)
    response = client.post("/api/product-chat", json={"message": "这个产品适合哪些行业？"})

    assert response.status_code == 200
    payload = response.json()
    assert "行业" in payload["answer"]
    assert payload["source"] in {"faq", "default", "llm"}
    assert not trace_path.exists()


def test_product_chat_uses_llm_when_configured(monkeypatch, tmp_path: Path):
    from app.config import paths
    from app.services import llm_client

    trace_path = tmp_path / "traces.jsonl"
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(llm_client, "is_deepseek_enabled", lambda: True)
    monkeypatch.setattr(
        llm_client,
        "generate_product_chat_answer",
        lambda message: f"LLM 产品回答：{message}",
    )

    client = TestClient(app)
    response = client.post("/api/product-chat", json={"message": "SupportPilot 能做什么？"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "llm"
    assert payload["answer"].startswith("LLM 产品回答：")
    assert not trace_path.exists()


def test_chat_stream_returns_final_event(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")

    client = TestClient(app)
    response = client.post(
        "/api/chat/stream",
        json={"customer_id": "shop_001", "message": "我的快递什么时候发货？"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_data_events(response.text)
    types = [event.get("type") for event in events]

    assert "step_start" in types
    assert "step_complete" in types
    assert types.count("final") == 1
    assert types.index("final") == len(types) - 1

    final_event = events[-1]
    assert final_event["response"]["action"] == "auto_reply"
    assert final_event["response"]["answer"]
    assert final_event["response"]["skill_calls"]
    assert final_event["response"]["memory_snapshot"]
    assert final_event["response"]["trace_id"]


def test_chat_stream_handoff_emits_manual_path_steps(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")

    client = TestClient(app)
    response = client.post(
        "/api/chat/stream",
        json={"customer_id": "shop_003", "message": "我要投诉并要求赔偿"},
    )

    assert response.status_code == 200
    events = _parse_sse_data_events(response.text)
    steps = [event["step"] for event in events if event.get("type") == "step_start"]

    assert "classify_intent" in steps
    assert "prepare_manual_answer" in steps
    assert events[-1]["type"] == "final"
    assert events[-1]["response"]["action"] == "handoff"


def test_knowledge_documents_returns_markdown_documents():
    client = TestClient(app)
    response = client.get("/api/knowledge/documents")

    assert response.status_code == 200
    documents = response.json()
    assert documents
    assert {doc["id"] for doc in documents} >= {"refund_policy", "shipping_policy"}
    first_document = documents[0]
    assert first_document["title"]
    assert first_document["category"]
    assert first_document["status"] == "enabled"
    assert first_document["source_type"] == "markdown"
    assert "usage_count" in first_document
    assert first_document["usage_count"] == 0


def test_knowledge_documents_usage_count_from_trace_citations(monkeypatch):
    from app.storage import repository

    monkeypatch.setattr(
        repository,
        "read_trace_rows",
        lambda: [
            {
                "citations": [
                    {"source": "refund_policy.md#退款规则", "snippet": "片段 A", "score": 0.9},
                    {"source": "shipping_policy.md#物流说明", "snippet": "片段 B", "score": 0.8},
                ]
            },
            {
                "citations": [
                    {"source": "refund_policy.md#退款规则", "snippet": "片段 A", "score": 0.9},
                ]
            },
        ],
    )

    client = TestClient(app)
    documents = client.get("/api/knowledge/documents").json()
    refund = next(doc for doc in documents if doc["id"] == "refund_policy")
    shipping = next(doc for doc in documents if doc["id"] == "shipping_policy")
    invoice = next(doc for doc in documents if doc["id"] == "invoice_policy")

    assert refund["usage_count"] == 2
    assert shipping["usage_count"] == 1
    assert invoice["usage_count"] == 0


def test_knowledge_document_crud(monkeypatch, tmp_path: Path):
    from app.services import knowledge_service

    monkeypatch.setattr(knowledge_service, "KB_DIR", tmp_path)
    (tmp_path / "refund_policy.md").write_text("# 退款规则\n\n用于测试。", encoding="utf-8")

    client = TestClient(app)

    create_response = client.post(
        "/api/knowledge/documents",
        json={
            "title": "SLA Policy",
            "category": "服务规范",
            "content": "响应时间说明",
            "status": "enabled",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == "sla_policy"
    assert created["content"].startswith("# SLA Policy")

    detail_response = client.get("/api/knowledge/documents/sla_policy")
    assert detail_response.status_code == 200
    assert detail_response.json()["category"] == "服务规范"

    update_response = client.patch(
        "/api/knowledge/documents/sla_policy",
        json={"status": "disabled", "content": "更新后的处理时效"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "disabled"
    assert "更新后的处理时效" in updated["content"]

    list_response = client.get("/api/knowledge/documents")
    assert list_response.status_code == 200
    listed = {doc["id"]: doc for doc in list_response.json()}
    assert listed["sla_policy"]["status"] == "disabled"

    delete_response = client.delete("/api/knowledge/documents/sla_policy")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"id": "sla_policy", "deleted": True}
    assert not (tmp_path / "sla_policy.md").exists()


def test_import_knowledge_markdown(monkeypatch, tmp_path: Path):
    from app.services import knowledge_service

    monkeypatch.setattr(knowledge_service, "KB_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/knowledge/documents/import",
        data={"category": "服务规范", "status": "enabled"},
        files={"file": ("service_policy.md", "# 服务政策\n\n## 处理时效\n\n标准请求会在 24 小时内响应。", "text/markdown")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "service_policy"
    assert payload["category"] == "服务规范"
    assert "标准请求" in payload["content"]
    assert (tmp_path / "service_policy.md").exists()


def test_import_knowledge_rejects_non_markdown(monkeypatch, tmp_path: Path):
    from app.services import knowledge_service

    monkeypatch.setattr(knowledge_service, "KB_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/knowledge/documents/import",
        files={"file": ("service_policy.txt", "not markdown", "text/plain")},
    )

    assert response.status_code == 400


    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    storage_path = tmp_path / "tickets.json"
    trace_row = {
        "trace_id": "trace_ticket_001",
        "customer_id": "shop_003",
        "intent": {"intent": "product_damage"},
        "ticket": {
            "ticket_id": "TICKET-TEST001",
            "title": "消费者反馈售后异常",
            "summary": "商品破损，需要补发",
            "priority": "P1",
            "status": "Open",
            "assignee": "售后专员A",
        },
        "created_at": "2026-06-17T10:00:00+00:00",
    }
    trace_path.write_text(json.dumps(trace_row, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(paths, "TICKETS_PATH", storage_path)

    client = TestClient(app)

    list_response = client.get("/api/tickets")
    assert list_response.status_code == 200
    tickets = list_response.json()
    assert len(tickets) == 1
    assert tickets[0]["ticket_id"] == "TICKET-TEST001"
    assert tickets[0]["status"] == "Open"

    update_response = client.patch(
        "/api/tickets/TICKET-TEST001",
        json={"status": "In Progress", "assignee": "售后主管B", "note": "优先复核补发流程"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "In Progress"
    assert updated["assignee"] == "售后主管B"
    assert updated["note"] == "优先复核补发流程"


def test_queue_records_and_convert_to_ticket(monkeypatch, tmp_path: Path):
    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    queue_path = tmp_path / "queue.json"
    tickets_path = tmp_path / "tickets.json"
    trace_row = {
        "trace_id": "trace_queue_001",
        "customer_id": "shop_007",
        "message": "我要投诉并要求人工联系我",
        "answer": "已转人工处理。",
        "action": "handoff",
        "intent": {"intent": "complaint_risk"},
        "risk": {"risk_level": "high", "reason": "涉及投诉，需要人工接管"},
        "created_at": "2026-06-17T10:00:00+00:00",
    }
    trace_path.write_text(json.dumps(trace_row, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(paths, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(paths, "TICKETS_PATH", tickets_path)

    client = TestClient(app)

    list_response = client.get("/api/queue")
    assert list_response.status_code == 200
    queue_rows = list_response.json()
    assert len(queue_rows) == 1
    assert queue_rows[0]["trace_id"] == "trace_queue_001"
    assert queue_rows[0]["status"] == "pending"

    update_response = client.patch(
        "/api/queue/trace_queue_001",
        json={"status": "in_progress", "assignee": "客服主管C", "note": "已接管处理中"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"

    create_ticket_response = client.post(
        "/api/queue/trace_queue_001/ticket",
        json={"assignee": "售后专员D", "priority": "P0", "note": "升级为工单"},
    )
    assert create_ticket_response.status_code == 201
    ticket = create_ticket_response.json()
    assert ticket["trace_id"] == "trace_queue_001"
    assert ticket["priority"] == "P0"

    queue_detail = client.get("/api/queue/trace_queue_001")
    assert queue_detail.status_code == 200
    assert queue_detail.json()["status"] == "ticket_created"
    assert queue_detail.json()["linked_ticket_id"] == ticket["ticket_id"]


def test_trace_detail_returns_trace_with_queue_and_ticket(monkeypatch, tmp_path: Path):
    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    queue_path = tmp_path / "queue.json"
    tickets_path = tmp_path / "tickets.json"
    trace_row = {
        "trace_id": "trace_detail_001",
        "customer_id": "shop_010",
        "message": "商品破损，要求人工处理",
        "answer": "已转人工处理。",
        "action": "create_ticket",
        "intent": {"intent": "product_damage"},
        "risk": {"risk_level": "high", "reason": "涉及售后风险"},
        "ticket": {
            "ticket_id": "TICKET-DETAIL001",
            "title": "消费者反馈售后异常",
            "summary": "商品破损，要求人工处理",
            "priority": "P0",
            "status": "Open",
            "assignee": "售后专员Z",
        },
        "created_at": "2026-06-18T10:00:00+00:00",
        "citations": [],
    }
    trace_path.write_text(json.dumps(trace_row, ensure_ascii=False) + "\n", encoding="utf-8")

    queue_payload = [
        {
            "trace_id": "trace_detail_001",
            "customer_id": "shop_010",
            "issue_type": "product_damage",
            "risk_level": "high",
            "risk_reason": "涉及售后风险",
            "message": "商品破损，要求人工处理",
            "answer": "已转人工处理。",
            "suggested_action": "接管 / 建工单",
            "status": "ticket_created",
            "assignee": "客服主管Y",
            "created_at": "2026-06-18T10:00:00+00:00",
            "updated_at": "2026-06-18T10:05:00+00:00",
            "note": "已转工单",
            "linked_ticket_id": "TICKET-DETAIL001",
        }
    ]
    tickets_payload = [
        {
            "ticket_id": "TICKET-DETAIL001",
            "trace_id": "trace_detail_001",
            "customer_id": "shop_010",
            "issue_type": "product_damage",
            "title": "消费者反馈售后异常",
            "summary": "商品破损，要求人工处理",
            "priority": "P0",
            "status": "Open",
            "assignee": "售后专员Z",
            "created_at": "2026-06-18T10:00:00+00:00",
            "updated_at": "2026-06-18T10:05:00+00:00",
            "note": "等待处理",
        }
    ]
    queue_path.write_text(json.dumps(queue_payload, ensure_ascii=False), encoding="utf-8")
    tickets_path.write_text(json.dumps(tickets_payload, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(paths, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(paths, "TICKETS_PATH", tickets_path)

    client = TestClient(app)

    response = client.get("/api/traces/trace_detail_001")
    assert response.status_code == 200
    payload = response.json()
    assert payload["trace"]["trace_id"] == "trace_detail_001"
    assert payload["queue"]["linked_ticket_id"] == "TICKET-DETAIL001"
    assert payload["ticket_record"]["ticket_id"] == "TICKET-DETAIL001"


def test_ticket_records_support_filters(monkeypatch, tmp_path: Path):
    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    storage_path = tmp_path / "tickets.json"
    trace_rows = [
        {
            "trace_id": "trace_ticket_001",
            "customer_id": "shop_003",
            "intent": {"intent": "product_damage"},
            "ticket": {
                "ticket_id": "TICKET-TEST001",
                "title": "ticket a",
                "summary": "summary a",
                "priority": "P1",
                "status": "Open",
                "assignee": "agent_a",
            },
            "created_at": "2026-06-17T10:00:00+00:00",
        },
        {
            "trace_id": "trace_ticket_002",
            "customer_id": "shop_004",
            "intent": {"intent": "complaint_risk"},
            "ticket": {
                "ticket_id": "TICKET-TEST002",
                "title": "ticket b",
                "summary": "summary b",
                "priority": "P0",
                "status": "In Progress",
                "assignee": "agent_b",
            },
            "created_at": "2026-06-17T11:00:00+00:00",
        },
    ]
    trace_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in trace_rows) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(paths, "TICKETS_PATH", storage_path)

    client = TestClient(app)

    response = client.get("/api/tickets", params={"status": "In Progress", "priority": "P0", "assignee": "agent_b"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["ticket_id"] == "TICKET-TEST002"

    response = client.get("/api/tickets", params={"issue_type": "product_damage"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["ticket_id"] == "TICKET-TEST001"


def test_queue_records_support_filters(monkeypatch, tmp_path: Path):
    from app.config import paths

    trace_path = tmp_path / "traces.jsonl"
    queue_path = tmp_path / "queue.json"
    trace_rows = [
        {
            "trace_id": "trace_queue_001",
            "customer_id": "shop_007",
            "message": "message a",
            "answer": "answer a",
            "action": "handoff",
            "intent": {"intent": "complaint_risk"},
            "risk": {"risk_level": "high", "reason": "reason a"},
            "created_at": "2026-06-17T10:00:00+00:00",
        },
        {
            "trace_id": "trace_queue_002",
            "customer_id": "shop_008",
            "message": "message b",
            "answer": "answer b",
            "action": "handoff",
            "intent": {"intent": "product_damage"},
            "risk": {"risk_level": "medium", "reason": "reason b"},
            "created_at": "2026-06-17T11:00:00+00:00",
        },
    ]
    trace_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in trace_rows) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "TRACE_PATH", trace_path)
    monkeypatch.setattr(paths, "QUEUE_PATH", queue_path)

    client = TestClient(app)

    update_response = client.patch(
        "/api/queue/trace_queue_002",
        json={"status": "in_progress", "assignee": "agent_q"},
    )
    assert update_response.status_code == 200

    response = client.get(
        "/api/queue",
        params={"status": "in_progress", "risk_level": "medium", "assignee": "agent_q"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["trace_id"] == "trace_queue_002"

    response = client.get("/api/queue", params={"issue_type": "complaint_risk"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["trace_id"] == "trace_queue_001"


# ---------------------------------------------------------------------------
#  Path traversal protection
# ---------------------------------------------------------------------------


def test_knowledge_document_path_traversal_blocked():
    """Path traversal attempts via document_id must be rejected with 400.

    FastAPI normalizes literal ``../`` in the URL path before routing, so
    those never reach our handler. This test uses invalid document_ids that
    DO survive routing but fail the _SAFE_DOCUMENT_ID_RE validation.
    """
    client = TestClient(app)
    # These values contain chars that fail the safe-id regex but survive
    # Starlette URL routing (which normalizes ``/`` and ``..`` away):
    #   ^[a-zA-Z0-9_][-a-zA-Z0-9_]*$
    invalid_ids = [
        "doc@sys",            # @ — not allowed
        ".hidden",            # leading dot
        "doc name",           # space
        "doc<script>x",       # angle brackets
    ]
    for doc_id in invalid_ids:
        response = client.get(f"/api/knowledge/documents/{doc_id}")
        assert response.status_code == 400, (
            f"document_id={doc_id!r} returned {response.status_code}, expected 400"
        )
        body = response.json()
        message = body.get("error", {}).get("message", "")
        assert "Invalid" in message or "invalid" in message.lower(), (
            f"Expected 'Invalid' in error message, got: {body}"
        )


def test_knowledge_document_delete_path_traversal_blocked():
    """Path traversal in DELETE must also be rejected for invalid document_id chars."""
    client = TestClient(app)
    response = client.delete("/api/knowledge/documents/.hidden")
    assert response.status_code == 400


def test_knowledge_document_valid_id_works():
    """A valid document_id (alphanumeric + underscores) must be accepted."""
    client = TestClient(app)
    # Create a document first so it exists
    create_payload = {
        "title": "Security Test Doc",
        "category": "test",
        "content": "## This is a test document for path traversal validation",
    }
    create_resp = client.post("/api/knowledge/documents", json=create_payload)
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["id"]

    # GET with valid id
    get_resp = client.get(f"/api/knowledge/documents/{doc_id}")
    assert get_resp.status_code == 200

    # Clean up
    delete_resp = client.delete(f"/api/knowledge/documents/{doc_id}")
    assert delete_resp.status_code == 200
