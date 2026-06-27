from __future__ import annotations

from datetime import datetime, timezone

from app.config import STORAGE_DIR, TICKETS_PATH, TRACE_PATH
from app.models.schemas import TicketRecord, TicketUpdateRequest
from app.storage import repository

__all__ = [
    "STORAGE_DIR",
    "TICKETS_PATH",
    "TRACE_PATH",
    "list_ticket_records",
    "get_ticket_record",
    "update_ticket_record",
    "count_ticket_records",
]


def list_ticket_records(
    status: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[TicketRecord]:
    stored_records = repository.read_ticket_store()
    trace_rows = repository.read_trace_rows()
    trace_ticket_ids = set()

    for row in trace_rows:
        ticket = row.get("ticket")
        if not ticket:
            continue
        ticket_id = ticket["ticket_id"]
        trace_ticket_ids.add(ticket_id)
        if ticket_id not in stored_records:
            stored_records[ticket_id] = _build_record_from_trace(row)

    repository.write_ticket_store(stored_records)
    records = list(stored_records.values())
    records = [
        item
        for item in records
        if _matches_ticket_filters(
            item,
            status=status,
            priority=priority,
            assignee=assignee,
            issue_type=issue_type,
        )
    ]
    records.sort(key=lambda item: item.updated_at, reverse=True)
    if limit is None:
        return records[offset:]
    return records[offset : offset + limit]


def count_ticket_records(
    status: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
) -> int:
    return len(
        list_ticket_records(
            status=status,
            priority=priority,
            assignee=assignee,
            issue_type=issue_type,
        )
    )


def get_ticket_record(ticket_id: str) -> TicketRecord:
    records = {item.ticket_id: item for item in list_ticket_records()}
    if ticket_id not in records:
        raise FileNotFoundError(ticket_id)
    return records[ticket_id]


def update_ticket_record(ticket_id: str, payload: TicketUpdateRequest) -> TicketRecord:
    records = repository.read_ticket_store()
    if ticket_id not in records:
        records = {item.ticket_id: item for item in list_ticket_records()}
    if ticket_id not in records:
        raise FileNotFoundError(ticket_id)

    current = records[ticket_id]
    updated = current.model_copy(
        update={
            "status": payload.status or current.status,
            "assignee": payload.assignee or current.assignee,
            "note": payload.note if payload.note is not None else current.note,
            "updated_at": _now_iso(),
        }
    )
    records[ticket_id] = updated
    repository.write_ticket_store(records)
    return updated


def _build_record_from_trace(row: dict) -> TicketRecord:
    ticket = row["ticket"]
    created_at = row.get("created_at") or _now_iso()
    return TicketRecord(
        ticket_id=ticket["ticket_id"],
        trace_id=row["trace_id"],
        customer_id=row["customer_id"],
        issue_type=row.get("intent", {}).get("intent", "unknown"),
        title=ticket["title"],
        summary=ticket["summary"],
        priority=ticket["priority"],
        status=ticket["status"],
        assignee=ticket["assignee"],
        created_at=created_at,
        updated_at=created_at,
        note="",
    )


def _matches_ticket_filters(
    record: TicketRecord,
    status: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
) -> bool:
    if status and record.status != status:
        return False
    if priority and record.priority != priority:
        return False
    if assignee and record.assignee != assignee:
        return False
    if issue_type and record.issue_type != issue_type:
        return False
    return True


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
