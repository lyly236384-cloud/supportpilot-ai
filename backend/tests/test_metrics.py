import json

import pytest

from app.services import metrics_service
from app.services.metrics_service import get_metrics, record_trace_metrics, rebuild_metrics_from_traces


@pytest.fixture(autouse=True)
def isolated_metrics(tmp_path, monkeypatch):
    snapshot = tmp_path / "logs" / "metrics_snapshot.json"
    monkeypatch.setattr(metrics_service, "METRICS_SNAPSHOT_PATH", snapshot)
    monkeypatch.setattr(metrics_service, "LOG_DIR", tmp_path / "logs")
    if snapshot.exists():
        snapshot.unlink()
    yield


def test_record_trace_metrics_increments_snapshot():
    record_trace_metrics("auto_reply", 120, 80)
    record_trace_metrics("handoff", 200, 100)
    record_trace_metrics("create_ticket", 300, 150)

    metrics = get_metrics()
    assert metrics.total_conversations == 3
    assert metrics.auto_reply_count == 1
    assert metrics.handoff_count == 1
    assert metrics.ticket_count == 1
    assert metrics.avg_elapsed_ms == pytest.approx((120 + 200 + 300) / 3, rel=0.01)
    assert metrics.total_estimated_tokens == 330


def test_rebuild_metrics_from_traces():
    rows = [
        {"action": "auto_reply", "elapsed_ms": 100, "estimated_tokens": 50},
        {"action": "create_ticket", "elapsed_ms": 250, "estimated_tokens": 120},
    ]
    metrics = rebuild_metrics_from_traces(rows)
    assert metrics.total_conversations == 2
    assert metrics.auto_reply_count == 1
    assert metrics.ticket_count == 1
    assert metrics.auto_resolution_rate == pytest.approx(0.5)

    assert metrics_service.METRICS_SNAPSHOT_PATH.exists()
    payload = json.loads(metrics_service.METRICS_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert payload["total_conversations"] == 2
