from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import PaginatedResponse, TicketRecord, TicketUpdateRequest
from app.services.ticket_service import (
    count_ticket_records,
    get_ticket_record,
    list_ticket_records,
    update_ticket_record,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("")
def tickets(
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    assignee: Optional[str] = Query(default=None),
    issue_type: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    envelope: bool = Query(default=False),
):
    records = list_ticket_records(
        status=status,
        priority=priority,
        assignee=assignee,
        issue_type=issue_type,
        limit=limit,
        offset=offset,
    )
    if envelope:
        total = count_ticket_records(
            status=status,
            priority=priority,
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


@router.get("/{ticket_id}", response_model=TicketRecord)
def ticket_detail(ticket_id: str) -> TicketRecord:
    try:
        return get_ticket_record(ticket_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}") from exc


@router.patch("/{ticket_id}", response_model=TicketRecord)
def update_ticket(ticket_id: str, payload: TicketUpdateRequest) -> TicketRecord:
    try:
        return update_ticket_record(ticket_id, payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}") from exc
