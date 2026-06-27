from __future__ import annotations

import json
import threading
from pathlib import Path

from app.config import LOG_DIR
from app.models.schemas import MetricsResponse
from app.storage import repository

METRICS_SNAPSHOT_PATH = LOG_DIR / "metrics_snapshot.json"
_lock = threading.Lock()

_DEFAULT_SNAPSHOT = {
    "total_conversations": 0,
    "auto_reply_count": 0,
    "handoff_count": 0,
    "ticket_count": 0,
    "total_elapsed_ms": 0,
    "total_estimated_tokens": 0,
}


def record_trace_metrics(action: str, elapsed_ms: int, estimated_tokens: int) -> None:
    with _lock:
        snapshot = _read_snapshot()
        snapshot["total_conversations"] += 1
        snapshot["total_elapsed_ms"] += elapsed_ms
        snapshot["total_estimated_tokens"] += estimated_tokens

        if action == "auto_reply":
            snapshot["auto_reply_count"] += 1
        elif action == "handoff":
            snapshot["handoff_count"] += 1
        elif action == "create_ticket":
            snapshot["ticket_count"] += 1

        _write_snapshot(snapshot)


def get_metrics() -> MetricsResponse:
    ensure_metrics_snapshot()
    with _lock:
        snapshot = _read_snapshot()
        total = snapshot["total_conversations"]
        auto_reply_count = snapshot["auto_reply_count"]
        handoff_count = snapshot["handoff_count"]
        ticket_count = snapshot["ticket_count"]

        return MetricsResponse(
            total_conversations=total,
            auto_reply_count=auto_reply_count,
            handoff_count=handoff_count,
            ticket_count=ticket_count,
            high_risk_count=repository.count_high_risk_traces(),
            auto_resolution_rate=round(auto_reply_count / total, 3) if total else 0,
            handoff_rate=round(handoff_count / total, 3) if total else 0,
            ticket_rate=round(ticket_count / total, 3) if total else 0,
            avg_elapsed_ms=round(snapshot["total_elapsed_ms"] / total, 2) if total else 0,
            total_estimated_tokens=snapshot["total_estimated_tokens"],
        )


def rebuild_metrics_from_traces(trace_rows: list[dict]) -> MetricsResponse:
    snapshot = dict(_DEFAULT_SNAPSHOT)
    for row in trace_rows:
        snapshot["total_conversations"] += 1
        snapshot["total_elapsed_ms"] += row.get("elapsed_ms", 0)
        snapshot["total_estimated_tokens"] += row.get("estimated_tokens", 0)
        action = row.get("action")
        if isinstance(action, dict):
            action = action.get("value") or action.get("intent")
        if action == "auto_reply":
            snapshot["auto_reply_count"] += 1
        elif action == "handoff":
            snapshot["handoff_count"] += 1
        elif action == "create_ticket":
            snapshot["ticket_count"] += 1

    with _lock:
        _write_snapshot(snapshot)
    return get_metrics()


def ensure_metrics_snapshot() -> None:
    snapshot = _read_snapshot()
    if snapshot["total_conversations"] > 0:
        return

    aggregated = repository.aggregate_trace_metrics()
    if aggregated["total_conversations"] > 0:
        with _lock:
            _write_snapshot(aggregated)


def rebuild_metrics_from_storage() -> MetricsResponse:
    aggregated = repository.aggregate_trace_metrics()
    with _lock:
        _write_snapshot(aggregated)
    return get_metrics()


def _read_snapshot() -> dict[str, int]:
    if not METRICS_SNAPSHOT_PATH.exists():
        return dict(_DEFAULT_SNAPSHOT)

    try:
        payload = json.loads(METRICS_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        merged = dict(_DEFAULT_SNAPSHOT)
        merged.update({key: int(payload.get(key, 0)) for key in _DEFAULT_SNAPSHOT})
        return merged
    except (json.JSONDecodeError, TypeError, ValueError):
        return dict(_DEFAULT_SNAPSHOT)


def _write_snapshot(snapshot: dict[str, int]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
