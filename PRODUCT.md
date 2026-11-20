# AI Agent

AI Agent is a self-hosted, context-aware assistant. The backend owns conversation state, memory, document retrieval, tool execution, and LLM calls; the frontend provides a focused chat workspace plus management screens for memories, documents, and settings.

## Objectives

- Produce clear, grounded answers using conversation history and user-owned context.
- Keep long-term memory explicit, reviewable, and editable.
- Keep business logic independent of UI components and API routes.
- Make provider calls, tools, and persistence testable without external services.
- Fail safely when credentials, providers, or tools are unavailable.

## Implemented Features

- **Chat**: token streaming over SSE, stop, regenerate, conversation title generation, message history, markdown/GFM/code rendering.
- **Context**: recent messages, user preferences, custom system prompt, retrieved memories, document chunks, optional web results.
- **Memory**: heuristic extraction from user messages, SHA-256 deduplication, CRUD, keyword/cosine retrieval, sensitive-data filtering.
- **Documents**: PDF/TXT/MD validation and extraction, overlap-aware chunking, embeddings, chunk search, deletion.
- **Tools**: calculator (AST-only, no `eval`), memory lookup, document search, optional Brave-compatible web search; tool calls are validated and read-only.
- **Agent**: provider-independent tool loop for non-streaming and streaming responses; no LangGraph dependency.
- **Configuration**: per-user preferences and model config; environment-driven defaults; OpenAI-compatible provider with chat/stream/embedding support.
- **Security**: `X-API-Key` auth, CORS allowlist, centralized structured errors, chat rate limiting, SSRF-safe tool inputs where applicable.
- **Operations**: Alembic migrations, health check, structured tests, SQLite fallback for tests, PostgreSQL for real use.

## Technology Stack

### Frontend

- React 19, TypeScript, Vite
- Tailwind CSS 4, React Router 7
- Vitest, React Testing Library
- react-markdown, remark-gfm, rehype-highlight

### Backend

- Python, FastAPI, Pydantic, Uvicorn
- SQLAlchemy 2, Alembic, PostgreSQL/psycopg
- OpenAI SDK (OpenAI-compatible endpoints)
- pypdf, python-multipart
- pytest, pytest-asyncio, httpx

## Architecture

```text
Browser (React + TypeScript)
  |  REST + SSE, X-API-Key
  v
FastAPI API routes + Pydantic schemas
  |  auth, validation, rate limit, structured errors
  v
Services
  |-- ChatService       orchestration, persistence, streaming
  |-- MemoryService     extraction, dedup, retrieval
  |-- DocumentService   upload, extract, chunk, embed, search
  |-- Preference/ModelConfig services
  v
Agent + Tools                  LLM Provider abstraction
  |-- calculator                |-- chat
  |-- memory lookup             |-- stream
  |-- document search           |-- embed
  |-- web search (optional)
  v
PostgreSQL (SQLAlchemy + Alembic)
```

## Request Flow

1. Frontend sends `POST /api/chat/stream` with content and optional conversation/regenerate IDs.
2. API validates input, authenticates the access token, and applies the rate limit.
3. `ChatService` resolves/creates the conversation, persists the user message, and builds context from preferences, memories, documents, and recent messages.
4. `AgentService` calls the configured LLM provider. If the provider returns tool calls, tools execute with validated arguments and results are fed back to the model.
5. Text deltas are stored and emitted as SSE events. The final assistant message is persisted; errors are marked on the message and emitted as an `error` event.
6. Frontend applies `started`/`delta`/`done`/`error` events to optimistic messages and refreshes the conversation list.

## Data Model

- `users`, `user_preferences`, `ai_model_configs`
- `conversations`, `messages`
- `memories`
- `documents`, `document_chunks`

Ownership is scoped by `user_id`; repositories reject cross-user access. Migrations live in `backend/alembic/versions`.

## Design Decisions

- **No mocked final AI**: the provider is real OpenAI-compatible code; tests use fakes only.
- **Provider independence**: app code depends on `LLMProvider`, not the OpenAI SDK.
- **Safe tools**: no arbitrary Python evaluation or shell commands; only registered read-only tools.
- **Plain PostgreSQL works**: embeddings are stored as JSON with in-process cosine ranking; no pgvector dependency is required.
- **Graceful degradation**: missing LLM key returns `llm_not_configured`; provider errors are mapped to stable error codes; failed streams persist an error message.
- **Testability**: services accept sessions/providers, API dependencies can be overridden, and tests default to in-memory SQLite.

## Known Limitations

- Web search requires a Brave-compatible API key and is disabled without one.
- Frontend production bundle is >500 kB (largely markdown/highlighting); route-level code splitting can be added if needed.
- `npm audit` currently reports 0 vulnerabilities for frontend dependencies.

## Product Status

The product has moved beyond the foundation phase: all core chat, memory, document, tool, provider, UI, and test layers described here are implemented and passing local automated verification. Remaining work is operational validation with real credentials/infrastructure and dependency hardening.
