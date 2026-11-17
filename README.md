# Personal AI Agent

Full-stack foundation for a personal, context-aware AI assistant. This phase includes project scaffolding, configuration, a health endpoint, database preparation, and tests. AI chat, memory, and LLM integration are intentionally not implemented yet.

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- PostgreSQL 14+
- Git

## Project Layout

```text
frontend/   React + TypeScript + Vite application
backend/    FastAPI application, database configuration, Alembic, tests
PRODUCT.md  Product overview and architecture
```

## Frontend Installation

```bash
cd frontend
npm install
```

## Backend Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.

## Environment Setup

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` and provide:

- `DATABASE_URL` - PostgreSQL SQLAlchemy connection URL.
- `LLM_API_KEY` - API key for the selected provider.
- `LLM_MODEL` - Model identifier.
- `LLM_BASE_URL` - Provider API base URL.
- `FRONTEND_URL` - Allowed browser origin for CORS.
- `BACKEND_URL` - Backend base URL.

Frontend environment variables must only use the `VITE_` prefix for values that are safe to expose. Never put API keys or database credentials in frontend files or `VITE_` variables.

## Database Setup

Create the PostgreSQL database manually, then set `DATABASE_URL` in `backend/.env`:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/personal_ai_agent
```

Run migrations from the backend directory:

```bash
cd backend
alembic upgrade head
```

No application tables are defined yet. Create a revision when the first model is added:

```bash
alembic revision --autogenerate -m "describe change"
```

## Development Commands

Frontend:

```bash
cd frontend
npm run dev
npm run build
npm run typecheck
```

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

The API health endpoint is `GET http://localhost:8000/api/health`.

## Testing Commands

Frontend:

```bash
cd frontend
npm test
```

Backend:

```bash
cd backend
pytest
```

## Branch and Commit Policy

Work on the existing `dev` branch. Do not commit generated environment files, virtual environments, build output, or secrets.
