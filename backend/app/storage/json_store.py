from __future__ import annotations

import json
from pathlib import Path

from app.config import LOG_DIR, QUEUE_PATH, STORAGE_DIR, TICKETS_PATH, TRACE_PATH
from app.models.schemas import QueueRecord, TicketRecord


def append_trace_row(row: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_trace_rows() -> list[dict]:
    if not TRACE_PATH.exists():
        return []

    rows: list[dict] = []
    for line in TRACE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def list_trace_rows(limit: int, offset: int) -> tuple[list[dict], int]:
    rows = read_trace_rows()
    total = len(rows)
    end = total - offset
    if end <= 0:
        return [], total
    start = max(0, end - limit)
    return rows[start:end], total


def get_trace_row(trace_id: str) -> dict | None:
    return next((row for row in read_trace_rows() if row.get("trace_id") == trace_id), None)


def read_queue_store() -> dict[str, QueueRecord]:
    if not QUEUE_PATH.exists():
        return {}

    raw_records = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    return {item["trace_id"]: QueueRecord(**item) for item in raw_records}


def write_queue_store(records: dict[str, QueueRecord]) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = [record.model_dump(mode="json") for record in records.values()]
    QUEUE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_ticket_store() -> dict[str, TicketRecord]:
    if not TICKETS_PATH.exists():
        return {}

    raw_records = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    return {item["ticket_id"]: TicketRecord(**item) for item in raw_records}


def write_ticket_store(records: dict[str, TicketRecord]) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = [record.model_dump(mode="json") for record in records.values()]
    TICKETS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def aggregate_trace_metrics() -> dict[str, int]:
    snapshot = dict(_DEFAULT_SNAPSHOT)
    for row in read_trace_rows():
        _accumulate_trace_row(snapshot, row)
    return snapshot


def _accumulate_trace_row(snapshot: dict[str, int], row: dict) -> None:
    snapshot["total_conversations"] += 1
    snapshot["total_elapsed_ms"] += int(row.get("elapsed_ms") or 0)
    snapshot["total_estimated_tokens"] += int(row.get("estimated_tokens") or 0)
    action = row.get("action")
    if action == "auto_reply":
        snapshot["auto_reply_count"] += 1
    elif action == "handoff":
        snapshot["handoff_count"] += 1
    elif action == "create_ticket":
        snapshot["ticket_count"] += 1
    risk_level = (row.get("risk") or {}).get("risk_level")
    if risk_level == "high":
        snapshot["high_risk_count"] += 1


_DEFAULT_SNAPSHOT = {
    "total_conversations": 0,
    "auto_reply_count": 0,
    "handoff_count": 0,
    "ticket_count": 0,
    "high_risk_count": 0,
    "total_elapsed_ms": 0,
    "total_estimated_tokens": 0,
}


def count_high_risk_traces() -> int:
    return sum(
        1
        for row in read_trace_rows()
        if (row.get("risk") or {}).get("risk_level") == "high"
    )


def legacy_files_exist() -> bool:
    return any(path.exists() for path in (TRACE_PATH, QUEUE_PATH, TICKETS_PATH))
