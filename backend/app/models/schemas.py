from enum import Enum
from typing import Any, Optional, TypedDict

from pydantic import BaseModel, Field


class Intent(str, Enum):
    LOGISTICS_QUESTION = "logistics_question"
    RETURN_REFUND = "return_refund"
    EXCHANGE_AFTER_SALE = "exchange_after_sale"
    INVOICE_QUESTION = "invoice_question"
    PRODUCT_DAMAGE = "product_damage"
    COMPLAINT_RISK = "complaint_risk"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Action(str, Enum):
    AUTO_REPLY = "auto_reply"
    HANDOFF = "handoff"
    CREATE_TICKET = "create_ticket"


class ConversationTurn(BaseModel):
    """One prior turn in the conversation, used for multi-turn context."""

    role: str = Field(..., description='"user" or "assistant"')
    content: str


class ChatRequest(BaseModel):
    customer_id: str = Field(default="cust_001", description="Mock customer id")
    message: str = Field(..., description="Customer question")
    history: list[ConversationTurn] = Field(
        default_factory=list,
        description="Prior conversation turns (oldest first), excluding the current message",
    )


class ProductChatRequest(BaseModel):
    message: str = Field(..., description="Homepage product question")


class ProductChatResponse(BaseModel):
    answer: str
    source: str = Field(default="default", description="llm, faq, or default")


class VerifierResult(BaseModel):
    passed: bool
    reason: str


class Citation(BaseModel):
    source: str
    snippet: str
    score: float = Field(ge=0.0, description="检索得分（关键词为命中数，向量/语义为相似度）")


class IntentResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0, description="意图置信度，0-1 之间")
    reason: str


class RiskResult(BaseModel):
    risk_level: RiskLevel
    requires_human: bool
    requires_ticket: bool
    reason: str


class Ticket(BaseModel):
    ticket_id: str
    title: str
    summary: str
    priority: str
    status: str
    assignee: str


class WorkflowStep(BaseModel):
    name: str
    status: str
    summary: str
    detail: str


class SkillCall(BaseModel):
    name: str
    purpose: str
    status: str
    input_summary: str
    output_summary: str


class MemorySnapshot(BaseModel):
    customer_id: str
    current_summary: str
    reusable_facts: list[str] = Field(default_factory=list)
    compressed_context: str


class ChatResponse(BaseModel):
    trace_id: str
    customer_id: str
    message: str
    intent: IntentResult
    risk: RiskResult
    action: Action
    answer: str
    citations: list[Citation]
    workflow_steps: list[WorkflowStep]
    ticket: Optional[Ticket] = None
    notification: Optional[dict[str, Any]] = None
    elapsed_ms: int = Field(ge=0, description="工作流耗时（毫秒）")
    estimated_tokens: int = Field(ge=0, description="估算 token 消耗")
    skill_calls: list[SkillCall] = Field(default_factory=list)
    memory_snapshot: Optional[MemorySnapshot] = None
    verifier_passed: Optional[bool] = None
    verifier_reason: str = ""


class KnowledgeReindexResponse(BaseModel):
    document_count: int = Field(ge=0, description="知识库文档数量")
    chunk_count: int = Field(ge=0, description="检索切片数量")
    retriever: str
    indexed_at: str


class MetricsResponse(BaseModel):
    total_conversations: int = Field(ge=0)
    auto_reply_count: int = Field(ge=0)
    handoff_count: int = Field(ge=0)
    ticket_count: int = Field(ge=0)
    high_risk_count: int = Field(ge=0, default=0)
    auto_resolution_rate: float = Field(ge=0.0, le=1.0)
    handoff_rate: float = Field(ge=0.0, le=1.0)
    ticket_rate: float = Field(ge=0.0, le=1.0)
    avg_elapsed_ms: float = Field(ge=0.0)
    total_estimated_tokens: int = Field(ge=0)


class MetricsTrendPoint(BaseModel):
    bucket: str
    total: int = Field(ge=0)
    auto_reply_count: int = Field(ge=0)
    auto_resolution_rate: float = Field(ge=0.0, le=1.0)


class MetricsTrendResponse(BaseModel):
    hours: int = Field(ge=1)
    granularity: str = "hour"
    points: list[MetricsTrendPoint]


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    category: str
    status: str
    source_type: str
    updated_at: str
    usage_count: Optional[int] = None
    preview: str


class KnowledgeDocumentDetail(KnowledgeDocument):
    content: str


class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str
    content: str
    status: str = "enabled"


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class DeleteResponse(BaseModel):
    id: str
    deleted: bool


class TicketRecord(BaseModel):
    ticket_id: str
    trace_id: str
    customer_id: str
    issue_type: str
    title: str
    summary: str
    priority: str
    status: str
    assignee: str
    created_at: str
    updated_at: str
    note: str = ""


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    note: Optional[str] = None


class QueueRecord(BaseModel):
    trace_id: str
    customer_id: str
    issue_type: str
    risk_level: str
    risk_reason: str
    message: str
    answer: str
    suggested_action: str
    status: str
    assignee: str
    created_at: str
    updated_at: str
    note: str = ""
    linked_ticket_id: str = ""


class QueueUpdateRequest(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    note: Optional[str] = None


class QueueTicketCreateRequest(BaseModel):
    assignee: Optional[str] = None
    priority: str = "P1"
    note: Optional[str] = None


class TraceDetailResponse(BaseModel):
    trace: dict[str, Any]
    queue: Optional[QueueRecord] = None
    ticket_record: Optional[TicketRecord] = None


class ApiError(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ApiError


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class WorkflowState(TypedDict, total=False):
    """LangGraph workflow state — accumulates partial results as nodes execute."""

    # --- inputs ---
    customer_id: str
    message: str
    trace_id: str
    history: list["ConversationTurn"]

    # --- llm / retrieval outputs ---
    intent: IntentResult
    risk: RiskResult
    citations: list[Citation]
    answer: str
    action: Action
    verifier: VerifierResult

    # --- tool execution ---
    customer: dict[str, Any]
    ticket: Optional[Ticket]
    notification: Optional[dict[str, Any]]

    # --- telemetry ---
    workflow_steps: list[WorkflowStep]
    skill_calls: list[SkillCall]
    memory_snapshot: MemorySnapshot
    start_time: float
    elapsed_ms: int
    estimated_tokens: int
    llm_token_usage: int
