# AI Agent

Full-stack, self-hosted personal assistant with streaming chat, long-term memory, document retrieval, safe tools, and an OpenAI-compatible LLM provider. The React frontend talks to a FastAPI backend that owns persistence, prompt assembly, tool execution, and provider calls.

## Features

- Streaming chat with Server-Sent Events (SSE), stop, and regenerate.
- Conversation history, search, rename, and delete.
- Long-term memories with deduplication, heuristic extraction, review, and retrieval.
- Document upload (PDF/TXT/MD), chunking, embeddings, and RAG context injection.
- Pluggable OpenAI-compatible chat, stream, and embedding provider.
- Read-only tools: calculator, saved-memory lookup, document search, optional web search.
- Per-user preferences and model configuration.
- API-key authentication, CORS, structured errors, and rate limiting.
- PostgreSQL persistence via SQLAlchemy/Alembic; SQLite in-memory fallback for tests.
- Dark/light UI with markdown, GFM tables, and syntax-highlighted code blocks.

## Project Layout

```text
frontend/   React + TypeScript + Vite application
backend/    FastAPI application, services, agent, tools, migrations, tests
PRODUCT.md  Product overview and architecture
```

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- PostgreSQL 14+
- Git

## Installation

```bash
cd frontend && npm install
cd ../backend && python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

## Environment Setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cd frontend && npm run sync-key
```

Backend values to set:

- `DATABASE_URL` - PostgreSQL SQLAlchemy URL.
- `APP_ACCESS_TOKEN` - long random token required in `X-API-Key` for private routes.
- `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` - real provider credentials. Without a key, chat returns `503 llm_not_configured`.
- `WEB_SEARCH_API_KEY` / `WEB_SEARCH_BASE_URL` - optional Brave-compatible search.
- `FRONTEND_URL` - allowed CORS origin for the frontend.
- `TEST_DATABASE_URL` - optional PostgreSQL URL for integration tests; leave empty for SQLite.

Frontend: `VITE_API_BASE_URL` sets the API origin. Run `npm run sync-key` in `frontend/` to copy `APP_ACCESS_TOKEN` from `backend/.env` into the gitignored `frontend/.env.local`; the app then sends it automatically and no key field appears in the UI. The browser bundle still contains this token, so do not expose this local app publicly. Never put the LLM key in a `VITE_` variable.

## Free Model Setup (OpenRouter)

For zero-cost chat, create a free key at https://openrouter.ai/keys and set these values in `backend/.env`:

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openrouter/free
LLM_API_KEY=<your OpenRouter key>
LLM_EMBEDDING_MODEL=
```

`openrouter/free` routes each request to an available free model. Free variants are rate-limited; OpenRouter documents the current limits in its free-model guide. Leaving `LLM_EMBEDDING_MODEL` blank disables paid embedding calls, so memories and documents use keyword retrieval instead.

## Database Setup

Create the database manually, then run:

```bash
cd /path/to/my-agent
createdb personal_ai_agent  # or use your PostgreSQL client
cd backend
alembic upgrade head
```

Create future revisions with:

```bash
alembic revision --autogenerate -m "describe change"
```

Retrieval stores embeddings as JSON and ranks with cosine similarity in Python, so a plain PostgreSQL database works. No pgvector extension or dependency is required.

## Running Locally

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd frontend
npm run dev
```

- Frontend: `http://localhost:5173`
- API health: `http://localhost:8000/api/health`
- OpenAPI docs: `http://localhost:8000/docs`

## API Overview

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/conversations` | Create conversation |
| `GET` | `/api/conversations` | List/search conversations |
| `GET` | `/api/conversations/{id}` | Get conversation |
| `PATCH` | `/api/conversations/{id}` | Rename |
| `DELETE` | `/api/conversations/{id}` | Delete |
| `GET` | `/api/conversations/{id}/messages` | List messages |
| `POST` | `/api/chat` | Non-streaming chat |
| `POST` | `/api/chat/stream` | SSE streaming chat |
| `GET`/`PATCH` | `/api/preferences` | Response preferences |
| `GET`/`PATCH` | `/api/model-config` | Model configuration (API only) |
| `GET`/`POST` | `/api/memories` | List/create memories |
| `PATCH`/`DELETE` | `/api/memories/{id}` | Update/delete memory |
| `GET`/`POST` | `/api/documents` | List/upload documents |
| `POST` | `/api/documents/search` | Search document chunks |
| `DELETE` | `/api/documents/{id}` | Delete document |

All routes except health require `X-API-Key: <APP_ACCESS_TOKEN>`. The frontend injects this header automatically from `frontend/.env.local`. Chat routes are rate-limited by `RATE_LIMIT_PER_MINUTE`.

SSE events are `started`, `delta`, `done`, and `error`; each block is a JSON payload prefixed with `data:`.

## Testing

```bash
cd backend
.venv/bin/python -m pytest -q

cd ../frontend
npm run typecheck
npm test -- --run
npm run build
```

Backend tests use mocked LLM providers and SQLite by default, so no external API key is required. Set `TEST_DATABASE_URL` to exercise PostgreSQL instead.

## Verification Status

- Backend suite: 36 tests passing.
- Frontend suite: 10 tests passing; typecheck and production build passing.
- Real OpenRouter free-model chat and streaming verified locally.

## Notes

- Environment files, virtual environments, uploads, and build output are gitignored.
- Work on the existing `dev` branch and keep secrets out of the repository.
