from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.models.schemas import MetricsResponse, MetricsTrendResponse, PaginatedResponse, TraceDetailResponse
from app.services.metrics_service import get_metrics, rebuild_metrics_from_storage
from app.services.metrics_trends_service import get_metrics_trends
from app.services.trace_export_service import build_traces_csv
from app.services.trace_service import get_trace_detail, list_trace_rows

router = APIRouter(prefix="/api", tags=["operations"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return get_metrics()


@router.post("/metrics/rebuild", response_model=MetricsResponse)
def rebuild_metrics() -> MetricsResponse:
    return rebuild_metrics_from_storage()


@router.get("/metrics/trends", response_model=MetricsTrendResponse)
def metrics_trends(hours: int = Query(default=24, ge=1, le=168)) -> MetricsTrendResponse:
    return get_metrics_trends(hours=hours)


@router.get("/traces")
def traces(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    envelope: bool = Query(default=False),
):
    rows, total = list_trace_rows(limit=limit, offset=offset)
    if envelope:
        return PaginatedResponse(items=rows, total=total, limit=limit, offset=offset)
    return rows


@router.get("/traces/export")
def export_traces(
    limit: Optional[int] = Query(default=None, ge=1, le=10000),
    all: bool = Query(default=False, alias="all"),
) -> Response:
    csv_content = build_traces_csv(limit=limit, export_all=all)
    return Response(
        content="\ufeff" + csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="supportpilot_traces.csv"'},
    )


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
def trace_detail(trace_id: str) -> TraceDetailResponse:
    try:
        return get_trace_detail(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}") from exc
