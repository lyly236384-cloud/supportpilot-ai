# Architecture Restructure Notes

## Goal

Separate frontend, backend, documents, scripts, tests, data, and runtime storage so later maintainers can locate errors by route path, component name, service name, schema name, or workflow step.

## New Top-Level Structure

```text
SupportPilot-AI-MVP/
  backend/
  frontend/
  docs/
  README.md
```

## Backend Responsibilities

- `backend/app/api/routes/`: FastAPI route handlers. Check here first for HTTP status, request path, response model, and route registration issues.
- `backend/app/config/`: central backend path/settings helpers. Check here for missing data files, wrong log location, and environment-dependent path bugs.
- `backend/app/models/`: Pydantic request/response schemas and workflow state contracts. Check here for validation and response serialization errors.
- `backend/app/workflow/`: AI workflow orchestration, LangGraph routing, trace writing, workflow steps.
- `backend/app/rag/`: retrieval strategy selection and knowledge base search implementations.
- `backend/app/services/`: LLM and external service clients.
- `backend/app/tools/`: mock tool adapters for customer profile, tickets, and notifications.
- `backend/app/memory/`: memory snapshot and context compression.
- `backend/app/agent/`: agent skill-call trace generation.
- `backend/app/ui/`: legacy Streamlit console. Keep separate from the React frontend.
- `backend/data/kb/`: sample knowledge base markdown files.
- `backend/data/mock/`: mock customer data.
- `backend/scripts/`: eval and retriever comparison scripts.
- `backend/tests/`: backend tests.
- `backend/storage/logs/`: runtime traces and generated reports.

## Frontend Responsibilities

- `frontend/src/app/`: app shell and page switching.
- `frontend/src/pages/`: route/page-level views.
- `frontend/src/components/layout/`: shared layout pieces such as logo and public navigation.
- `frontend/src/components/widgets/`: cross-page widgets such as online consultation.
- `frontend/src/features/skills-showcase/`: skills showcase feature UI and data.
- `frontend/src/features/workbench/`: workbench module data and future business screens.
- `frontend/src/services/`: API request wrappers. API errors should not be debugged inside pages.
- `frontend/src/hooks/`: reusable state hooks.
- `frontend/src/types/`: frontend contract constants and future schema/types.
- `frontend/src/styles/`: global Tailwind styles.

## Moved Files

- `app/` -> `backend/app/`
- `data/` -> `backend/data/`
- `scripts/` -> `backend/scripts/`
- `tests/` -> `backend/tests/`
- `storage/` -> `backend/storage/`
- `requirements.txt` -> `backend/requirements.txt`
- `.env.example` -> `backend/.env.example`
- `.env` -> `backend/.env`
- `frontend/src/components/SkillsShowcase.jsx` -> `frontend/src/features/skills-showcase/components/SkillsShowcase.jsx`
- `frontend/src/components/Logo.jsx` -> `frontend/src/components/layout/Logo.jsx`
- `frontend/src/components/PublicNav.jsx` -> `frontend/src/components/layout/PublicNav.jsx`
- `frontend/src/components/ConsultWidget.jsx` -> `frontend/src/components/widgets/ConsultWidget.jsx`
- `frontend/src/pages/HomePage.jsx` -> `frontend/src/pages/home/HomePage.jsx`
- `frontend/src/pages/WorkbenchPage.jsx` -> `frontend/src/pages/workbench/WorkbenchPage.jsx`
- `frontend/src/styles.css` -> `frontend/src/styles/global.css`
- `frontend/src/App.jsx` -> `frontend/src/app/App.jsx`

## Split Files

- `backend/app/main.py` was reduced to app creation and router registration.
- `backend/app/api/routes/chat.py` now owns `/api/chat` and `/api/chat/stream`.
- `backend/app/api/routes/metrics.py` now owns `/api/metrics` and `/api/traces`.
- `backend/app/api/routes/health.py` now owns `/`.
- `backend/app/config/paths.py` centralizes backend data and storage paths.
- `frontend/src/data/product.js` was split into:
  - `frontend/src/components/layout/navigationData.js`
  - `frontend/src/features/skills-showcase/data/skills.js`
  - `frontend/src/features/workbench/data/modules.js`

## Updated References

- Backend data paths now use `app.config.paths`.
- `backend/app/rag/base.py` uses `KB_DIR`.
- `backend/app/tools/mock_tools.py` uses `MOCK_DATA_DIR`.
- `backend/app/workflow/orchestrator.py` uses `LOG_DIR`.
- Backend scripts now resolve `BACKEND_ROOT`.
- Frontend imports now point to the new app/pages/components/features structure.
- README startup commands now use `backend/` as the backend working directory.

## Error Location Rules

- `404` or wrong API path: `backend/app/api/routes/`
- response validation error: `backend/app/models/schemas.py`
- workflow step failure: `backend/app/workflow/orchestrator.py`
- RAG missing or wrong citation: `backend/app/rag/` and `backend/data/kb/`
- mock customer/ticket error: `backend/app/tools/` and `backend/data/mock/`
- trace or metrics mismatch: `backend/storage/logs/` and `backend/app/api/routes/metrics.py`
- frontend page render error: `frontend/src/pages/`
- reusable UI error: `frontend/src/components/`
- skills showcase UI error: `frontend/src/features/skills-showcase/`
- frontend API error: `frontend/src/services/`
- frontend page state error: `frontend/src/hooks/`

## Architecture Risks

- Python package name remains `app` for low-risk migration. A future rename to `backend.app` would require broader import updates.
- Streamlit remains as a legacy console under `backend/app/ui/`. Long term, duplicate UI surfaces should be reduced after React reaches feature parity.
- LLM service, prompt logic, and mock fallback still live in one large `llm_client.py`. It should be split by provider and by task.
- Workflow orchestration remains a large file. It should later be split into nodes, routing, response assembly, and tracing.
- Runtime log files in project root may remain if old running processes still hold them. They are ignored by git.
- `npm audit` reports Vite/esbuild high severity with no direct fix available in the current dependency chain. Recheck before deployment.

## Future Performance Work

- Cache knowledge base loading and vector tokenization.
- Avoid rebuilding LangGraph workflow for every request.
- Add pagination and server-side filtering for traces.
- Introduce frontend code splitting if business pages become large.
- Add API response caching for read-only metrics.

## Future Maintenance Work

- Add OpenAPI-generated frontend types or a shared contract generation step.
- Add `backend/app/api/dependencies/` when authentication is introduced.
- Add `backend/app/repositories/` and `backend/app/migrations/` when replacing JSON/mock storage with a database.
- Add `backend/app/tasks/` if async jobs or queues are introduced.
- Add feature modules for `auth`, `users`, `support`, `knowledge-base`, `tickets`, and `admin` as real domains are implemented.
