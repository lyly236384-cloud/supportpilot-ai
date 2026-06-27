import json

import pytest

from app.config import paths
from app.storage import repository


@pytest.fixture
def isolated_sqlite_db(monkeypatch, tmp_path):
    db_path = tmp_path / "supportpilot_test.db"
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setattr(paths, "SQLITE_PATH", db_path)
    repository.init_storage()
    return db_path


def test_sqlite_trace_pagination(isolated_sqlite_db):
    for index in range(3):
        repository.append_trace_row(
            {
                "trace_id": f"trace_{index}",
                "customer_id": "shop_001",
                "message": f"message {index}",
                "action": "auto_reply",
            }
        )

    page, total = repository.list_trace_rows(limit=2, offset=0)
    assert total == 3
    assert len(page) == 2
    assert page[-1]["trace_id"] == "trace_2"

    page_offset, _ = repository.list_trace_rows(limit=2, offset=2)
    assert len(page_offset) == 1
    assert page_offset[0]["trace_id"] == "trace_0"


def test_sqlite_queue_and_ticket_roundtrip(isolated_sqlite_db):
    from app.models.schemas import QueueRecord, TicketRecord

    queue_record = QueueRecord(
        trace_id="trace_q1",
        customer_id="shop_002",
        issue_type="complaint_risk",
        risk_level="high",
        risk_reason="投诉",
        message="我要投诉",
        answer="已转人工",
        suggested_action="接管",
        status="pending",
        assignee="agent_a",
        created_at="2026-06-18T10:00:00+00:00",
        updated_at="2026-06-18T10:00:00+00:00",
    )
    repository.write_queue_store({"trace_q1": queue_record})

    ticket_record = TicketRecord(
        ticket_id="TICKET-Q1",
        trace_id="trace_q1",
        customer_id="shop_002",
        issue_type="complaint_risk",
        title="投诉工单",
        summary="我要投诉",
        priority="P1",
        status="Open",
        assignee="agent_a",
        created_at="2026-06-18T10:00:00+00:00",
        updated_at="2026-06-18T10:00:00+00:00",
    )
    repository.write_ticket_store({"TICKET-Q1": ticket_record})

    queue_rows = repository.read_queue_store()
    ticket_rows = repository.read_ticket_store()
    assert queue_rows["trace_q1"].status == "pending"
    assert ticket_rows["TICKET-Q1"].ticket_id == "TICKET-Q1"


def test_sqlite_aggregate_trace_metrics(isolated_sqlite_db):
    for index in range(2):
        repository.append_trace_row(
            {
                "trace_id": f"trace_metric_{index}",
                "customer_id": "shop_001",
                "message": f"message {index}",
                "action": "auto_reply" if index == 0 else "handoff",
                "elapsed_ms": 100 + index,
                "estimated_tokens": 50 + index,
            }
        )

    metrics = repository.aggregate_trace_metrics()
    assert metrics["total_conversations"] == 2
    assert metrics["auto_reply_count"] == 1
    assert metrics["handoff_count"] == 1
    assert metrics["high_risk_count"] == 0
    assert metrics["total_elapsed_ms"] == 201
    assert metrics["total_estimated_tokens"] == 101
