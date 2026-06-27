from __future__ import annotations

from app.config.settings import use_sqlite_storage
from app.models.schemas import QueueRecord, TicketRecord
from app.storage import json_store, sqlite_store


def init_storage() -> None:
    if use_sqlite_storage():
        sqlite_store.init_db()
        sqlite_store.migrate_from_legacy_files()

    from app.services.metrics_service import ensure_metrics_snapshot

    ensure_metrics_snapshot()


def append_trace_row(row: dict) -> None:
    _backend().append_trace_row(row)


def read_trace_rows() -> list[dict]:
    return _backend().read_trace_rows()


def list_trace_rows(limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    return _backend().list_trace_rows(limit, offset)


def get_trace_row(trace_id: str) -> dict | None:
    return _backend().get_trace_row(trace_id)


def read_queue_store() -> dict[str, QueueRecord]:
    return _backend().read_queue_store()


def write_queue_store(records: dict[str, QueueRecord]) -> None:
    _backend().write_queue_store(records)


def read_ticket_store() -> dict[str, TicketRecord]:
    return _backend().read_ticket_store()


def write_ticket_store(records: dict[str, TicketRecord]) -> None:
    _backend().write_ticket_store(records)


def aggregate_trace_metrics() -> dict[str, int]:
    return _backend().aggregate_trace_metrics()


def count_high_risk_traces() -> int:
    return _backend().count_high_risk_traces()


def _backend():
    return sqlite_store if use_sqlite_storage() else json_store
