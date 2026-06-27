# SupportPilot AI Homepage API Contracts

## 1. Purpose

This document covers homepage-only APIs that are **not** part of the customer-service workbench workflow.

Key rule: homepage product chat must **not** write customer-service trace logs (`/api/chat` traces).

Related workbench contracts: `docs/workbench_api_contracts.md`

## 2. Base Rules

- Frontend base URL: `http://127.0.0.1:5173`
- Backend base URL default: `http://127.0.0.1:8000`
- Request wrapper: `frontend/src/services/apiClient.js`
- API entry: `frontend/src/services/supportApi.js` → `sendProductChatMessage()`
- UI component: `frontend/src/components/widgets/ConsultWidget.jsx`
- State hook: `frontend/src/hooks/useProductChat.js`

## 3. `POST /api/product-chat`

Purpose:

- answer marketing / product questions on the homepage consult widget
- separate from `/api/chat` customer workflow (no trace persistence)

Request body:

```json
{
  "message": "这个产品适合哪些行业？"
}
```

Response body:

```json
{
  "answer": "SupportPilot AI 适用于需要统一承接客户咨询...",
  "source": "faq"
}
```

`source` values:

| Value | Meaning |
|-------|---------|
| `faq` | Matched built-in product FAQ keyword rules |
| `llm` | Generated via DeepSeek when `LLM_PROVIDER=deepseek` and API key is configured |
| `default` | Fallback product overview when no FAQ / LLM match |

Answer priority:

1. LLM (when DeepSeek enabled and call succeeds)
2. FAQ keyword rules (`backend/app/services/product_chat_service.py`)
3. Default product overview text

Side effects:

- **none** — must not append to `traces.jsonl` / SQLite traces table
- does not create queue records or tickets

Failure:

- uses shared error envelope from workbench doc (`error.code`, `error.message`)
- validation error (`422`) when `message` is missing

Frontend flow:

1. User submits question in `ConsultWidget`
2. `useProductChat` calls `sendProductChatMessage({ message })`
3. Assistant bubble renders `answer`; errors surface via hook `error` state

## 4. Environment

Product chat LLM path follows global backend LLM config:

```env
LLM_PROVIDER=mock          # FAQ + default only (no LLM source)
LLM_PROVIDER=deepseek        # enables source=llm when DEEPSEEK_API_KEY is set
DEEPSEEK_API_KEY=
```

With `LLM_PROVIDER=mock`, responses use FAQ rules or the default overview — suitable for demos without API balance.

## 5. Tests

Coverage:

- `backend/tests/test_api.py::test_product_chat_returns_answer_without_writing_trace`
- `backend/tests/test_api.py::test_product_chat_uses_llm_when_configured`

Assertions:

- `200` response with `answer` and `source`
- trace storage file remains empty after product-chat calls
