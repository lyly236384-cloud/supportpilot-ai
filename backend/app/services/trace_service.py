from __future__ import annotations

from app.models.schemas import TraceDetailResponse
from app.services.queue_service import list_queue_records
from app.services.ticket_service import list_ticket_records
from app.storage import repository


def list_trace_rows(limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    return repository.list_trace_rows(limit=limit, offset=offset)


def get_trace_detail(trace_id: str) -> TraceDetailResponse:
    trace_row = repository.get_trace_row(trace_id)
    if not trace_row:
        raise FileNotFoundError(trace_id)

    queue_record = next((item for item in list_queue_records() if item.trace_id == trace_id), None)
    ticket_id = (trace_row.get("ticket") or {}).get("ticket_id") or (queue_record.linked_ticket_id if queue_record else "")
    ticket_record = next((item for item in list_ticket_records() if item.ticket_id == ticket_id), None)

    return TraceDetailResponse(
        trace=trace_row,
        queue=queue_record,
        ticket_record=ticket_record,
    )
