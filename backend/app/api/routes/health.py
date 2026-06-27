from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "SupportPilot AI",
        "description": "AI customer service operations platform MVP",
        "docs": "http://127.0.0.1:8000/docs",
    }
