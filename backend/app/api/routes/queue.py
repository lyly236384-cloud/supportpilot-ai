from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import PaginatedResponse, QueueRecord, QueueTicketCreateRequest, QueueUpdateRequest, TicketRecord
from app.services.queue_service import (
    count_queue_records,
    create_queue_ticket,
    get_queue_record,
    list_queue_records,
    update_queue_record,
)

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("")
def queue_records(
    status: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    assignee: Optional[str] = Query(default=None),
    issue_type: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    envelope: bool = Query(default=False),
):
    records = list_queue_records(
        status=status,
        risk_level=risk_level,
        assignee=assignee,
        issue_type=issue_type,
        limit=limit,
        offset=offset,
    )
    if envelope:
        total = count_queue_records(
            status=status,
            risk_level=risk_level,
            assignee=assignee,
            issue_type=issue_type,
        )
        return PaginatedResponse(
            items=records,
            total=total,
            limit=limit or total,
            offset=offset,
        )
    return records


@router.get("/{trace_id}", response_model=QueueRecord)
def queue_detail(trace_id: str) -> QueueRecord:
    try:
        return get_queue_record(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Queue record not found: {trace_id}") from exc


@router.patch("/{trace_id}", response_model=QueueRecord)
def update_queue(trace_id: str, payload: QueueUpdateRequest) -> QueueRecord:
    try:
        return update_queue_record(trace_id, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Queue record not found: {trace_id}") from exc


@router.post("/{trace_id}/ticket", response_model=TicketRecord, status_code=201)
def queue_to_ticket(trace_id: str, payload: QueueTicketCreateRequest) -> TicketRecord:
    try:
        return create_queue_ticket(trace_id, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Queue record not found: {trace_id}") from exc
