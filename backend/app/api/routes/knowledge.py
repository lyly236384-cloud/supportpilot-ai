from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import (
    DeleteResponse,
    KnowledgeDocument,
    KnowledgeDocumentCreate,
    KnowledgeDocumentDetail,
    KnowledgeDocumentUpdate,
)
from app.services.knowledge_service import (
    create_knowledge_document,
    delete_knowledge_document,
    get_knowledge_document,
    import_knowledge_markdown,
    list_knowledge_documents,
    reindex_knowledge_base,
    update_knowledge_document,
)
from app.models.schemas import KnowledgeReindexResponse

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=list[KnowledgeDocument])
def knowledge_documents() -> list[KnowledgeDocument]:
    return list_knowledge_documents()


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetail)
def knowledge_document_detail(document_id: str) -> KnowledgeDocumentDetail:
    try:
        return get_knowledge_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Knowledge document not found: {document_id}") from exc


@router.post("/documents", response_model=KnowledgeDocumentDetail, status_code=201)
def create_document(payload: KnowledgeDocumentCreate) -> KnowledgeDocumentDetail:
    try:
        return create_knowledge_document(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/documents/import", response_model=KnowledgeDocumentDetail, status_code=201)
async def import_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    category: str | None = Form(default=None),
    status: str = Form(default="enabled"),
) -> KnowledgeDocumentDetail:
    try:
        return import_knowledge_markdown(
            filename=file.filename or "knowledge.md",
            content_bytes=await file.read(),
            title=title,
            category=category,
            status=status,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "already exists" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.patch("/documents/{document_id}", response_model=KnowledgeDocumentDetail)
def update_document(document_id: str, payload: KnowledgeDocumentUpdate) -> KnowledgeDocumentDetail:
    try:
        return update_knowledge_document(document_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Knowledge document not found: {document_id}") from exc


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str) -> DeleteResponse:
    try:
        delete_knowledge_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Knowledge document not found: {document_id}") from exc
    return DeleteResponse(id=document_id, deleted=True)


@router.post("/reindex", response_model=KnowledgeReindexResponse)
def reindex_knowledge() -> KnowledgeReindexResponse:
    return reindex_knowledge_base()
