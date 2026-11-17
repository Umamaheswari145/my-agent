# Personal AI Agent

Personal AI Agent is a full-stack application for building a private, context-aware AI assistant. This repository currently contains the initial development foundation only; AI behavior, memory, and LLM integration are planned for later phases.

## Objectives

- Understand user questions and produce clear, accurate, meaningful responses.
- Maintain conversation context across turns.
- Remember useful information with explicit, reviewable storage.
- Keep business logic independent from UI components and API routes.
- Provide a reliable, testable base for incremental feature development.

## Planned Features

- Conversational interface with message history.
- Server-side conversation orchestration.
- Context management and long-term memory.
- Pluggable LLM provider configuration through environment variables.
- Health checks, structured errors, and database migrations.
- Automated frontend and backend test suites.

## Technology Stack

### Frontend

- React, TypeScript, Vite
- Tailwind CSS
- React Router
- Vitest, React Testing Library

### Backend

- Python, FastAPI, Pydantic
- Uvicorn
- SQLAlchemy, Alembic
- PostgreSQL
- Pytest

## High-Level Architecture

```text
Browser (React + TypeScript)
        |
        | HTTP / JSON
        v
FastAPI application
        |
        |-- API routes and Pydantic schemas
        |-- Service and agent layers (reserved for future logic)
        |-- Centralized error handling
        |
        v
PostgreSQL
        ^
        |
     Alembic migrations
```

The frontend handles presentation and routing only. The backend owns configuration, validation, persistence, and future AI/business logic. PostgreSQL is the only application database.
