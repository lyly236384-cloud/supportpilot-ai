from fastapi import APIRouter

from app.tools.mock_tools import get_customer_profile, list_all_customers

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def customer_list():
    return list_all_customers()


@router.get("/{customer_id}")
def customer_detail(customer_id: str):
    return get_customer_profile(customer_id)
