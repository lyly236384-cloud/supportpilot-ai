from fastapi import APIRouter, Query

from app.services.seed_service import seed_demo_data

router = APIRouter(prefix="/api/seed", tags=["seed"])


@router.post("")
def seed(force: bool = Query(default=False)):
    return seed_demo_data(force=force)
