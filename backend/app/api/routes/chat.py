from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.workflow.orchestrator import run_support_stream, run_support_workflow

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return run_support_workflow(request.customer_id, request.message, request.history)


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        try:
            async for event in run_support_stream(
                request.customer_id, request.message, request.history
            ):
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event, ensure_ascii=False, default=str),
                }
        except Exception as exc:
            _logger.exception("SSE stream error for customer %s", request.customer_id)
            yield {
                "event": "error",
                "data": json.dumps(
                    {"type": "error", "message": "Internal stream error"},
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(event_generator())
