from __future__ import annotations

from datetime import datetime, timezone

from app.config import QUEUE_PATH, STORAGE_DIR, TRACE_PATH
from app.models.schemas import QueueRecord, QueueTicketCreateRequest, QueueUpdateRequest, TicketRecord
from app.services.ticket_service import get_ticket_record, list_ticket_records
from app.storage import repository

__all__ = ["QUEUE_PATH", "STORAGE_DIR", "TRACE_PATH", "list_queue_records", "get_queue_record", "update_queue_record", "create_queue_ticket"]


def list_queue_records(
    status: str | None = None,
    risk_level: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[QueueRecord]:
    stored_records = repository.read_queue_store()
    trace_rows = repository.read_trace_rows()

    for row in trace_rows:
        if row.get("action") != "handoff":
            continue
        trace_id = row["trace_id"]
        if trace_id not in stored_records:
            stored_records[trace_id] = _build_record_from_trace(row)

    repository.write_queue_store(stored_records)
    records = list(stored_records.values())
    records = [
        item
        for item in records
        if _matches_queue_filters(
            item,
            status=status,
            risk_level=risk_level,
            assignee=assignee,
            issue_type=issue_type,
        )
    ]
    records.sort(key=lambda item: item.updated_at, reverse=True)
    if limit is None:
        return records[offset:]
    return records[offset : offset + limit]


def count_queue_records(
    status: str | None = None,
    risk_level: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
) -> int:
    return len(
        list_queue_records(
            status=status,
            risk_level=risk_level,
            assignee=assignee,
            issue_type=issue_type,
        )
    )


def get_queue_record(trace_id: str) -> QueueRecord:
    records = {item.trace_id: item for item in list_queue_records()}
    if trace_id not in records:
        raise FileNotFoundError(trace_id)
    return records[trace_id]


def update_queue_record(trace_id: str, payload: QueueUpdateRequest) -> QueueRecord:
    records = repository.read_queue_store()
    if trace_id not in records:
        records = {item.trace_id: item for item in list_queue_records()}
    if trace_id not in records:
        raise FileNotFoundError(trace_id)

    current = records[trace_id]
    updated = current.model_copy(
        update={
            "status": payload.status or current.status,
            "assignee": payload.assignee or current.assignee,
            "note": payload.note if payload.note is not None else current.note,
            "updated_at": _now_iso(),
        }
    )
    records[trace_id] = updated
    repository.write_queue_store(records)
    return updated


def create_queue_ticket(trace_id: str, payload: QueueTicketCreateRequest) -> TicketRecord:
    queue_record = get_queue_record(trace_id)
    existing_ticket_id = queue_record.linked_ticket_id
    if existing_ticket_id:
        update_queue_record(
            trace_id,
            QueueUpdateRequest(
                status="ticket_created",
                assignee=payload.assignee or queue_record.assignee,
                note=payload.note if payload.note is not None else queue_record.note,
            ),
        )
        return get_ticket_record(existing_ticket_id)

    queue_records = repository.read_queue_store()
    if trace_id not in queue_records:
        queue_records = {item.trace_id: item for item in list_queue_records()}

    ticket = _create_ticket_from_queue(queue_record, payload)
    ticket_records = {item.ticket_id: item for item in list_ticket_records()}
    ticket_records[ticket.ticket_id] = ticket
    repository.write_ticket_store(ticket_records)

    queue_records[trace_id] = queue_record.model_copy(
        update={
            "status": "ticket_created",
            "assignee": payload.assignee or queue_record.assignee,
            "note": payload.note if payload.note is not None else queue_record.note,
            "linked_ticket_id": ticket.ticket_id,
            "updated_at": _now_iso(),
        }
    )
    repository.write_queue_store(queue_records)
    return ticket


def _build_record_from_trace(row: dict) -> QueueRecord:
    created_at = row.get("created_at") or _now_iso()
    customer_id = row.get("customer_id", "")
    default_assignee = "人工客服待分配"
    return QueueRecord(
        trace_id=row["trace_id"],
        customer_id=customer_id,
        issue_type=row.get("intent", {}).get("intent", "unknown"),
        risk_level=row.get("risk", {}).get("risk_level", "high"),
        risk_reason=row.get("risk", {}).get("reason", ""),
        message=row.get("message", ""),
        answer=row.get("answer", ""),
        suggested_action="接管 / 建工单",
        status="pending",
        assignee=default_assignee,
        created_at=created_at,
        updated_at=created_at,
        note="",
        linked_ticket_id=(row.get("ticket") or {}).get("ticket_id", ""),
    )


def _create_ticket_from_queue(queue_record: QueueRecord, payload: QueueTicketCreateRequest) -> TicketRecord:
    created_at = _now_iso()
    return TicketRecord(
        ticket_id=f"TICKET-{queue_record.trace_id[-6:].upper()}",
        trace_id=queue_record.trace_id,
        customer_id=queue_record.customer_id,
        issue_type=queue_record.issue_type,
        title="人工队列转服务工单",
        summary=queue_record.message,
        priority=payload.priority,
        status="Open",
        assignee=payload.assignee or queue_record.assignee,
        created_at=created_at,
        updated_at=created_at,
        note=payload.note or "",
    )


def _matches_queue_filters(
    record: QueueRecord,
    status: str | None = None,
    risk_level: str | None = None,
    assignee: str | None = None,
    issue_type: str | None = None,
) -> bool:
    if status and record.status != status:
        return False
    if risk_level and record.risk_level != risk_level:
        return False
    if assignee and record.assignee != assignee:
        return False
    if issue_type and record.issue_type != issue_type:
        return False
    return True


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
