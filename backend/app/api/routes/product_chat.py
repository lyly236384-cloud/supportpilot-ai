from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ProductChatRequest, ProductChatResponse
from app.services.product_chat_service import answer_product_question

router = APIRouter(prefix="/api", tags=["product"])


@router.post("/product-chat", response_model=ProductChatResponse)
def product_chat(request: ProductChatRequest) -> ProductChatResponse:
    result = answer_product_question(request.message)
    return ProductChatResponse(answer=result.answer, source=result.source)
