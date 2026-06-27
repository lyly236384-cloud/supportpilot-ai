# SupportPilot AI Workbench API Contracts

## 1. Purpose

This document is the current source of truth for workbench frontend-backend integration.

It focuses on:

- workbench module to API mapping
- request and response contracts
- current status enums and field meanings
- frontend integration entry points

It does not describe visual layout. Its purpose is to keep UI optimization and backend integration decoupled.

## 2. Base Rules

- Frontend base URL: `http://127.0.0.1:5173`
- Backend base URL default: `http://127.0.0.1:8000`
- Frontend request wrapper: `frontend/src/services/apiClient.js`
  - `requestJson` — JSON APIs + error envelope parsing
  - `requestChatStream` — SSE parser for `/api/chat/stream`
- Frontend business API entry: `frontend/src/services/supportApi.js`
- Workbench page shell: `frontend/src/pages/workbench/WorkbenchPage.jsx`
- Workbench data hook: `frontend/src/features/workbench/hooks/useWorkbenchData.js`
- Homepage product chat contract: `docs/homepage_api_contracts.md`

## 2.1 Shared Response Envelopes

### Paginated list (`envelope=true`)

Used by `GET /api/traces`, `GET /api/queue`, and `GET /api/tickets`.

```json
{
  "items": [],
  "total": 42,
  "limit": 15,
  "offset": 0
}
```

Common query params:

- `limit`: page size (workbench UI uses `15`; API max `200` when set)
- `offset`: zero-based row offset
- `envelope`: when `true`, returns the wrapper above instead of a bare array

### Error envelope

All registered HTTP, validation, and `FileNotFoundError` handlers return:

```json
{
  "error": {
    "code": "http_404",
    "message": "Trace not found: trace_xxx"
  }
}
```

Common `error.code` values:

| Code | HTTP | Meaning |
|------|------|---------|
| `http_404` | 404 | Resource not found (queue, ticket, trace, knowledge doc) |
| `http_422` | 422 | Request validation failed |
| `validation_error` | 422 | Pydantic / query validation failure |
| `not_found` | 404 | Unhandled `FileNotFoundError` |

Frontend parser: `frontend/src/services/apiClient.js` reads `error.message`.

## 3. Workbench Module Mapping

### 3.1 数据概览

Frontend module:

- `overview`

Primary APIs:

- `GET /api/metrics`
- `POST /api/metrics/rebuild`

Current frontend usage:

- hero stats (`metrics.handoff_count`, `metrics.ticket_count`)
- summary cards
- risk summary (`metrics.high_risk_count`)
- rebuild metrics action

### 3.2 人工队列

Frontend module:

- `queue`

Primary APIs:

- `GET /api/queue?limit=&offset=&envelope=true`
- `GET /api/queue/{trace_id}`
- `PATCH /api/queue/{trace_id}`
- `POST /api/queue/{trace_id}/ticket`

Current frontend usage:

- paginated queue list (15 per page) with filters
- queue detail panel
- takeover status update
- assignee update
- handling note update
- convert queue record to service ticket

### 3.3 处理记录

Frontend module:

- `records`

Primary APIs:

- `GET /api/traces?limit=&offset=&envelope=true`
- `GET /api/traces/{trace_id}`
- `GET /api/traces/export?all=true`

Current frontend usage:

- paginated trace list (15 per page)
- trace detail panel
- export all traces as CSV

### 3.4 服务工单

Frontend module:

- `tickets`

Primary APIs:

- `GET /api/tickets?limit=&offset=&envelope=true`
- `GET /api/tickets/{ticket_id}`
- `PATCH /api/tickets/{ticket_id}`

Current frontend usage:

- paginated ticket list (15 per page) with filters
- ticket detail panel
- status update
- assignee update
- note update

### 3.5 知识库

Frontend module:

- `knowledge`

Primary APIs:

- `GET /api/knowledge/documents`
- `GET /api/knowledge/documents/{document_id}`
- `POST /api/knowledge/documents`
- `PATCH /api/knowledge/documents/{document_id}`
- `DELETE /api/knowledge/documents/{document_id}`
- `POST /api/knowledge/reindex`

Current frontend usage:

- document list
- document detail
- create
- edit
- enable / disable
- delete
- rebuild knowledge index

## 4. Shared Enums

### 4.1 Chat Action

Defined in:

- `backend/app/models/schemas.py`
- `frontend/src/types/apiContracts.js`

Values:

- `auto_reply`
- `handoff`
- `create_ticket`

### 4.2 Risk Level

Defined in backend schema:

- `low`
- `medium`
- `high`

### 4.3 Queue Status

Current frontend and backend usage:

- `pending`
- `in_progress`
- `resolved`
- `ticket_created`

Recommendation:

- treat these as current product enums
- keep UI labels mapped separately in frontend

### 4.4 Ticket Status

Current frontend options:

- `Open`
- `In Progress`
- `Resolved`
- `Closed`

Recommendation:

- keep exact casing stable until backend enum is formalized

## 5. API Contracts

## 5.1 `POST /api/chat`

Purpose:

- run the support workflow for a customer message

Request body:

```json
{
  "customer_id": "cust_001",
  "message": "我的快递什么时候发货？"
}
```

Response body:

```json
{
  "trace_id": "trace_xxx",
  "customer_id": "cust_001",
  "message": "我的快递什么时候发货？",
  "intent": {
    "intent": "logistics_question",
    "confidence": 0.88,
    "reason": "命中物流或配送关键词"
  },
  "risk": {
    "risk_level": "low",
    "requires_human": false,
    "requires_ticket": false,
    "reason": "普通售后咨询，可尝试自动回复"
  },
  "action": "auto_reply",
  "answer": "根据知识库资料...",
  "citations": [
    {
      "source": "shipping_policy.md#发货时效",
      "snippet": "...",
      "score": 3.5
    }
  ],
  "workflow_steps": [],
  "ticket": null,
  "notification": null,
  "elapsed_ms": 24,
  "estimated_tokens": 221,
  "skill_calls": [],
  "memory_snapshot": null
}
```

Frontend use:

- not currently used by workbench page
- used for support workflow integration and future detail views

## 5.2 `POST /api/chat/stream`

Purpose:

- stream support workflow progress as Server-Sent Events (SSE)
- **writes a customer-service trace** on successful completion (same as `POST /api/chat`)
- must **not** be used for homepage product chat (`POST /api/product-chat`)

Transport:

- `Content-Type: text/event-stream`
- each SSE frame uses `event: <type>` and `data: <json>`
- `data` is UTF-8 JSON with `ensure_ascii=False`

Request body:

- same as `POST /api/chat` (`ChatRequest`)

```json
{
  "customer_id": "shop_001",
  "message": "我的快递什么时候发货？"
}
```

Engine selection:

- controlled by `LLM_WORKFLOW_ENGINE` env (`procedural` default, or `langgraph`)
- both engines emit the same top-level event `type` values documented below

### Event types

| `type` | When emitted | Purpose |
|--------|----------------|---------|
| `step_start` | Before a workflow node runs | UI step timeline — running state |
| `step_complete` | After a workflow node finishes | UI step timeline — completed state + summary |
| `final` | Once at end of stream | Full `ChatResponse` payload; stream ends |

### `step_start`

```json
{
  "type": "step_start",
  "step": "classify_intent",
  "display": "1. 意图识别"
}
```

Fields:

- `step`: internal node key (stable for logic)
- `display`: human-readable label for UI

Known `step` keys (procedural engine order may skip some nodes):

| `step` | `display` |
|--------|-----------|
| `classify_intent` | 1. 意图识别 |
| `check_risk` | 2. 风险判断 |
| `retrieve_knowledge` | 3. 知识库检索 |
| `generate_answer` / `prepare_manual_answer` | 4. 生成回复 |
| `verify_answer` | 5. 答复校验 |
| `decide_action` | 6. 动作决策 |
| `execute_tools` | 7. 工具执行 |
| `finalize` | 8. 组装响应 |

### `step_complete`

```json
{
  "type": "step_complete",
  "step": "classify_intent",
  "display": "1. 意图识别",
  "output": {
    "summary": "识别为 logistics_question，置信度 0.88",
    "detail": "命中物流或配送关键词"
  }
}
```

`output` is a display-oriented object. Common shapes:

- intent step: `{ "summary": "识别为 …", "detail": "<reason>" }`
- risk step: `{ "summary": "风险等级 high", "detail": "<reason>" }`
- retrieve step: `{ "summary": "命中 N 条知识片段", "detail": "…" }`
- verify step: `{ "summary": "通过" \| "未通过", "detail": "<verifier reason>" }`
- execute_tools: `{ "summary": "已创建工单并发送通知" }` when applicable

Some procedural steps may return `{ "summary": "回复已生成" }` only.

### `final`

```json
{
  "type": "final",
  "response": {
    "trace_id": "trace_abc123",
    "customer_id": "shop_001",
    "message": "我的快递什么时候发货？",
    "intent": { "intent": "logistics_question", "confidence": 0.88, "reason": "…" },
    "risk": {
      "risk_level": "low",
      "requires_human": false,
      "requires_ticket": false,
      "reason": "…"
    },
    "action": "auto_reply",
    "answer": "根据知识库资料…",
    "citations": [{ "source": "shipping_policy.md#…", "snippet": "…", "score": 3.5 }],
    "workflow_steps": [
      { "name": "1. 意图识别", "status": "completed", "summary": "…", "detail": "…" }
    ],
    "ticket": null,
    "notification": null,
    "elapsed_ms": 24,
    "estimated_tokens": 221,
    "skill_calls": [],
    "memory_snapshot": { "customer_id": "shop_001", "current_summary": "…", "reusable_facts": [], "compressed_context": "…" },
    "verifier_passed": true,
    "verifier_reason": ""
  }
}
```

`response` matches `ChatResponse` from section 5.1. `action` values:

- `auto_reply`
- `handoff`
- `create_ticket`

Side effects:

- `_log_trace(response)` runs before the `final` event is sent
- increments metrics snapshot and persists trace row

Failure:

- HTTP errors before stream starts use the shared error envelope (section 2.1)
- mid-stream failures are not currently modeled as SSE error events; connection may abort

### Typical procedural event sequence

```
step_start   → classify_intent
step_complete → classify_intent
step_start   → check_risk
step_complete → check_risk
step_start   → retrieve_knowledge
step_complete → retrieve_knowledge
step_start   → generate_answer | prepare_manual_answer
step_complete → …
step_start   → verify_answer        (skipped on manual path)
step_complete → verify_answer       (skipped on manual path)
step_start   → execute_tools        (only when action = create_ticket)
step_complete → execute_tools       (only when action = create_ticket)
final
```

### Frontend integration

Parser:

- `frontend/src/services/apiClient.js` → `requestChatStream(payload, onEvent)`
- reads `data:` lines, `JSON.parse`, invokes `onEvent(event)` per frame

State hook:

- `frontend/src/hooks/useSupportChat.js`
  - `streamEvents`: raw events + client `receivedAt` offset
  - `steps`: derived running/completed steps from `step_*` events; replaced by `response.workflow_steps` on `final`
  - `result`: `event.response` from `final`

UI:

- `frontend/src/features/workbench/components/DebugDrawer.jsx`
- `frontend/src/features/workbench/components/shared/StreamEventTimeline.jsx`

On `final`, workbench calls `workbenchData.refresh()` to reload metrics / queue / tickets.

## 5.3 `GET /api/metrics`

Purpose:

- return aggregate operating metrics from trace logs

Response body:

```json
{
  "total_conversations": 146,
  "auto_reply_count": 83,
  "handoff_count": 34,
  "ticket_count": 29,
  "high_risk_count": 5,
  "auto_resolution_rate": 0.568,
  "handoff_rate": 0.233,
  "ticket_rate": 0.199,
  "avg_elapsed_ms": 344.65,
  "total_estimated_tokens": 32001
}
```

Frontend use:

- `WorkbenchHero`
- `OverviewPanel`

## 5.3.1 `POST /api/metrics/rebuild`

Purpose:

- recompute aggregate metrics from persisted trace storage (SQLite or JSON)

Response body:

- same shape as `GET /api/metrics`

Frontend use:

- `OverviewPanel` rebuild metrics action

## 5.4 `GET /api/traces`

Purpose:

- return workflow trace rows with optional pagination envelope

Query params:

- `limit`: integer, optional, default `50`, max `200` when not using envelope
- `offset`: integer, optional, default `0`
- `envelope`: boolean, optional, default `false` — when `true`, returns paginated wrapper

Example:

- `GET /api/traces?limit=15&offset=0&envelope=true`

Paginated response body:

```json
{
  "items": [],
  "total": 146,
  "limit": 15,
  "offset": 0
}
```

Legacy response (no envelope):

- array of raw trace objects

Current frontend normalization:

- `frontend/src/features/workbench/utils/normalizeTrace.js`

Frontend use:

- records list (paginated)
- trace detail drawer

## 5.4.2 `GET /api/traces/export`

Purpose:

- download trace rows as UTF-8 CSV (with BOM) for operations export

Query params:

- `all`: boolean, optional, default `false` — when `true`, export all traces via server-side pagination (500 rows per batch)
- `limit`: integer, optional — when `all` is false and `limit` omitted, defaults to `2000`; max `10000`

Example:

- `GET /api/traces/export?all=true`

Response:

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="supportpilot_traces.csv"`

CSV columns:

- `trace_id`, `customer_id`, `message`, `intent`, `risk_level`, `action`, `elapsed_ms`, `estimated_tokens`, `answer`, `created_at`

Frontend use:

- `RecordsPanel` export all CSV action

## 5.5 `GET /api/knowledge/documents`

Purpose:

- return lightweight knowledge document list

Response body:

```json
[
  {
    "id": "refund_policy",
    "title": "退款规则",
    "category": "服务政策",
    "status": "enabled",
    "source_type": "markdown",
    "updated_at": "2026-06-12T15:37:57+00:00",
    "usage_count": null,
    "preview": "退货质检通过后..."
  }
]
```

Query params:

- `status`: optional exact match
- `priority`: optional exact match
- `assignee`: optional exact match
- `issue_type`: optional exact match

Example:

- `GET /api/tickets?status=Open&priority=P1`

Frontend use:

- knowledge list table

## 5.4.1 `GET /api/traces/{trace_id}`

Purpose:

- return one trace record detail enriched with queue and ticket relations

Response body:

```json
{
  "trace": {
    "trace_id": "trace_detail_001",
    "customer_id": "shop_010",
    "message": "商品破损，要求人工处理",
    "action": "create_ticket"
  },
  "queue": {
    "trace_id": "trace_detail_001",
    "status": "ticket_created",
    "assignee": "客服主管Y",
    "linked_ticket_id": "TICKET-DETAIL001"
  },
  "ticket_record": {
    "ticket_id": "TICKET-DETAIL001",
    "status": "Open",
    "assignee": "售后专员Z",
    "note": "等待处理"
  }
}
```

Failure:

- `404` when trace not found

Frontend use:

- intended for records detail drawer
- can also support cross-link detail views from queue and ticket modules

## 5.6 `GET /api/knowledge/documents/{document_id}`

Purpose:

- return full knowledge document detail

Response body:

```json
{
  "id": "refund_policy",
  "title": "退款规则",
  "category": "服务政策",
  "status": "enabled",
  "source_type": "markdown",
  "updated_at": "2026-06-12T15:37:57+00:00",
  "usage_count": null,
  "preview": "退货质检通过后...",
  "content": "# 退款规则\n\n..."
}
```

Frontend use:

- knowledge detail panel
- knowledge edit preload

Failure:

- `404` when document not found

## 5.7 `POST /api/knowledge/documents`

Purpose:

- create a new knowledge document stored as markdown

Request body:

```json
{
  "title": "SLA Policy",
  "category": "服务规范",
  "content": "响应时间说明",
  "status": "enabled"
}
```

Response body:

- same shape as `KnowledgeDocumentDetail`

Failure:

- `409` when generated document id already exists

Frontend use:

- knowledge create form

## 5.8 `PATCH /api/knowledge/documents/{document_id}`

Purpose:

- update part of a knowledge document

Request body:

```json
{
  "status": "disabled",
  "content": "更新后的处理时效"
}
```

Response body:

- same shape as `KnowledgeDocumentDetail`

Failure:

- `404` when document not found

Frontend use:

- knowledge edit form
- enable / disable action

## 5.9 `DELETE /api/knowledge/documents/{document_id}`

Purpose:

- delete a knowledge document

Response body:

```json
{
  "id": "sla_policy",
  "deleted": true
}
```

Failure:

- `404` when document not found

Frontend use:

- knowledge delete action

## 5.9.1 `POST /api/knowledge/reindex`

Purpose:

- rebuild the RAG chunk index from all enabled knowledge markdown documents

Response body:

```json
{
  "document_count": 12,
  "chunk_count": 48,
  "retriever": "hybrid",
  "indexed_at": "2026-06-18T12:00:00+00:00"
}
```

Frontend use:

- `KnowledgePanel`「重建索引」action via `reindexKnowledgeBase()`

## 5.10 `GET /api/tickets`

Purpose:

- return structured service ticket records with optional filters and pagination

Query params:

- `status`: optional exact match (`Open`, `In Progress`, `Resolved`, `Closed`)
- `priority`: optional exact match (`P0`–`P3`)
- `assignee`: optional exact match
- `issue_type`: optional exact match
- `limit`: optional page size, max `200`
- `offset`: optional, default `0`
- `envelope`: optional, default `false`

Examples:

- `GET /api/tickets?status=Open&priority=P1`
- `GET /api/tickets?limit=15&offset=0&envelope=true&status=Open`

Legacy response (no envelope):

```json
[
  {
    "ticket_id": "TICKET-TEST001",
    "trace_id": "trace_ticket_001",
    "customer_id": "shop_003",
    "issue_type": "product_damage",
    "title": "消费者反馈售后异常",
    "summary": "商品破损，需要补发",
    "priority": "P1",
    "status": "Open",
    "assignee": "售后专员A",
    "created_at": "2026-06-17T10:00:00+00:00",
    "updated_at": "2026-06-17T10:00:00+00:00",
    "note": ""
  }
]
```

Paginated response (`envelope=true`):

- same shape as shared `PaginatedResponse`; `items` are `TicketRecord` objects

Frontend use:

- `TicketsPanel` paginated list with `fetchTicketsPage`
- `useWorkbenchData` initial load via `fetchTickets()` (unpaginated snapshot)

## 5.11 `GET /api/tickets/{ticket_id}`

Purpose:

- return one ticket detail

Response body:

- same shape as `TicketRecord`

Failure:

- `404` when ticket not found

Frontend use:

- reserved for future standalone ticket detail view

## 5.12 `PATCH /api/tickets/{ticket_id}`

Purpose:

- update ticket status, assignee, or note

Request body:

```json
{
  "status": "In Progress",
  "assignee": "售后主管B",
  "note": "优先复核补发流程"
}
```

Response body:

- same shape as `TicketRecord`

Failure:

- `404` when ticket not found

Frontend use:

- tickets operation panel

## 5.13 `GET /api/queue`

Purpose:

- return structured handoff queue records with optional filters and pagination

Query params:

- `status`: optional exact match (`pending`, `in_progress`, `resolved`, `ticket_created`)
- `risk_level`: optional exact match (`high`, `medium`, `low`)
- `assignee`: optional exact match
- `issue_type`: optional exact match
- `limit`: optional page size, max `200`
- `offset`: optional, default `0`
- `envelope`: optional, default `false`

Examples:

- `GET /api/queue?status=pending&risk_level=high`
- `GET /api/queue?limit=15&offset=0&envelope=true&status=in_progress`

Legacy response (no envelope):

```json
[
  {
    "trace_id": "trace_queue_001",
    "customer_id": "shop_007",
    "issue_type": "complaint_risk",
    "risk_level": "high",
    "risk_reason": "涉及投诉，需要人工接管",
    "message": "我要投诉并要求人工联系我",
    "answer": "已转人工处理。",
    "suggested_action": "接管 / 建工单",
    "status": "pending",
    "assignee": "人工客服待分配",
    "created_at": "2026-06-17T10:00:00+00:00",
    "updated_at": "2026-06-17T10:00:00+00:00",
    "note": "",
    "linked_ticket_id": ""
  }
]
```

Paginated response (`envelope=true`):

- same shape as shared `PaginatedResponse`; `items` are `QueueRecord` objects

Frontend use:

- `QueuePanel` paginated list with `fetchQueueRecordsPage`
- `useWorkbenchData` initial load via `fetchQueueRecords()` (unpaginated snapshot)
- queue detail panel

## 5.14 `GET /api/queue/{trace_id}`

Purpose:

- return one queue record detail

Response body:

- same shape as `QueueRecord`

Failure:

- `404` when queue record not found

Frontend use:

- reserved for future dedicated detail fetch

## 5.15 `PATCH /api/queue/{trace_id}`

Purpose:

- update queue processing status, assignee, or note

Request body:

```json
{
  "status": "in_progress",
  "assignee": "客服主管C",
  "note": "已接管处理中"
}
```

Response body:

- same shape as `QueueRecord`

Failure:

- `404` when queue record not found

Frontend use:

- queue operation panel
- mark as in progress
- mark as resolved
- assign queue owner

## 5.16 `POST /api/queue/{trace_id}/ticket`

Purpose:

- convert a queue record into a service ticket

Request body:

```json
{
  "assignee": "售后专员D",
  "priority": "P0",
  "note": "升级为工单"
}
```

Response body:

- same shape as `TicketRecord`

Side effect:

- queue status becomes `ticket_created`
- `linked_ticket_id` is written back to queue record

Failure:

- `404` when queue record not found

Frontend use:

- queue panel `建工单` action

## 6. Frontend Integration Entry Points

### 6.1 Request Wrappers

File:

- `frontend/src/services/supportApi.js`

Current exported calls:

- `sendChatMessage`
- `fetchMetrics`
- `rebuildMetrics`
- `fetchTraces`
- `fetchTracesPage`
- `downloadTracesExport`
- `fetchTraceDetail`
- `fetchKnowledgeDocuments`
- `fetchKnowledgeDocument`
- `createKnowledgeDocument`
- `updateKnowledgeDocument`
- `deleteKnowledgeDocument`
- `reindexKnowledgeBase`
- `fetchTickets`
- `fetchTicketsPage`
- `updateTicket`
- `fetchQueueRecords`
- `fetchQueueRecordsPage`
- `updateQueueRecord`
- `reindexKnowledgeBase`

Streaming (not in `supportApi.js`):

- `requestChatStream` in `frontend/src/services/apiClient.js`

### 6.2 Page State Aggregation

File:

- `frontend/src/features/workbench/hooks/useWorkbenchData.js`

Current aggregated state:

- `metrics`
- `knowledgeDocuments`
- `tickets`
- `queueRecords`
- `metricsPending` / `metricsError`
- loading and per-module mutation states

### 6.3 Workbench Module Entry

Files:

- `frontend/src/features/workbench/components/moduleMeta.js`
- `frontend/src/features/workbench/components/WorkbenchBody.jsx`

Current module keys:

- `overview`
- `queue`
- `records`
- `tickets`
- `knowledge`

## 7. Current Frontend-to-API Mapping

### 7.1 `OverviewPanel`

Uses:

- `metrics` (including `high_risk_count`)
- `rebuildMetrics`

### 7.2 `QueuePanel`

Uses:

- `fetchQueueRecordsPage` (paginated, with filters)
- `updateQueueRecord`
- `createTicketFromQueue`

### 7.3 `RecordsPanel`

Uses:

- `fetchTracesPage` (paginated)
- `fetchTraceDetail`
- `downloadTracesExport({ all: true })`

### 7.4 `TicketsPanel`

Uses:

- `fetchTicketsPage` (paginated, with filters)
- `updateTicket`

### 7.5 `KnowledgePanel`

Uses:

- `knowledgeDocuments`
- `fetchKnowledgeDocument`
- `createKnowledgeDocument`
- `updateKnowledgeDocument`
- `deleteKnowledgeDocument`
- `reindexKnowledgeBase`

### 7.6 `DebugDrawer` (workbench shell)

Uses:

- `useSupportChat` → `requestChatStream` (`POST /api/chat/stream`)
- `StreamEventTimeline` for `streamEvents`
- `workbenchData.refresh()` on stream `final`

## 8. Known Gaps

Remaining integration gaps (not blocking current MVP):

- explicit filter enum reference tables for queue / ticket status values (section 4 lists casing but not full semantics)
- homepage product chat is documented in `docs/homepage_api_contracts.md` (out of workbench scope)

## 9. Suggested Next Backend Contract

Next highest-value contracts:

- formal OpenAPI / JSON Schema export for `ChatResponse` and paginated envelopes
- optional SSE `error` event type for mid-stream failure reporting

## 10. Usage Guidance

When optimizing frontend UI after this point:

- do not redesign state shape first
- use this contract document as the stable integration layer
- only add new frontend visual structure around existing API payloads unless a new endpoint is explicitly introduced

If a page needs a new interaction, define the backend contract here first, then cut the UI against that contract.
