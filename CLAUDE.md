# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VitAI Backend is a FastAPI service that analyzes food product images using OpenAI's multimodal API to return nutritional information and health scores. It stores results in Supabase PostgreSQL and caches them in Redis.

## Commands

This project uses `uv` (Rust-based package manager) and `make` for common tasks:

```bash
make install      # Install production dependencies
make dev          # Install all dependencies including dev
make run          # Start dev server (uvicorn --reload on :8000)
make test         # Run tests with -v
make test-cov     # Run tests with coverage report
make lint         # Ruff check (no autofix)
make format       # Ruff format + ruff check --fix
make check-all    # lint + test (mirrors pre-commit)
```

Run a single test:
```bash
uv run pytest tests/test_ai_endpoint.py -v
uv run pytest tests/ -k "test_health" -v
```

Docker stack (PostgreSQL 15, Redis 7, API):
```bash
docker-compose up -d
docker-compose logs -f api
```

Database migrations:
```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Architecture

**Request flow:** Routes (thin, input validation only) → Controllers (business logic, orchestration) → Services/Repositories → Database/External APIs

**Key directories:**
- `app/api/v1/` — HTTP endpoints (routes only, no logic)
- `app/controllers/` — Business logic; `analysis_controller.py` is the core: deduplicates by image hash, checks Redis cache, calls OpenAI, persists result
- `app/services/` — External integrations: `openai_service.py`, `redis_service.py`, `image_service.py`
- `app/db/repositories/` — Data access layer; keeps all SQL out of controllers
- `app/db/models/` — SQLAlchemy ORM models (`Analysis`, `AiConsumptionMetric`, `PromptVersion`)
- `app/models/` — Pydantic schemas for API request/response
- `app/core/` — Cross-cutting: security, rate limiting, exceptions
- `app/middleware/` — Metrics middleware assigns anonymous `session_id` UUID cookie per visitor

## Critical Design Decisions

**Supabase + PgBouncer (transaction mode):** The database engine uses `NullPool` and `prepared_statement_cache_size=0`. Do not change these — Supabase routes through PgBouncer which does not support server-side prepared statements or persistent connections. See `app/db/session.py`.

**Redis circuit breaker:** `redis_service.py` wraps all cache operations so that if Redis is unavailable the API degrades gracefully (cache miss, no error). Never assume Redis is available.

**Image deduplication:** `analysis_controller.py` hashes the incoming image bytes and skips OpenAI if an identical hash is already in the DB. This is the primary cost-saving mechanism.

**Prompt versioning:** AI prompts are stored in the `prompt_versions` table (not hardcoded). Only one version per language can be `active=True` at a time. The `prompt_controller.py` loads the active prompt with a TTL cache to avoid per-request DB queries. Prompt templates as markdown files live in `app/services/prompts/`.

**Anonymous sessions:** There are no user accounts. The metrics middleware sets a `session_id` UUID cookie (1-year TTL, HttpOnly, Secure in prod). All analytics and history are keyed to this session.

**OpenAI response parsing:** Uses `model_validate` (Pydantic v2) for parsing structured responses from OpenAI. See `openai_service.py`.

## Authentication

API key format: `vitai_sk_prod_<random_urlsafe_32_chars>`. Validated in `app/core/security.py` using `secrets.compare_digest` (timing-safe). The key is passed as `X-API-Key` header.

## Environment

Copy `.env.example` to `.env`. Required variables:
- `OPEN_AI_KEY` — OpenAI API key
- `API_KEY` — Service API key (format above)
- `DATABASE_URL` — PostgreSQL connection string (Supabase)
- `REDIS_URL` — Redis connection string

`APP_ENV` controls behavior: `development` skips HTTPS redirect and Trusted Host middleware; `production` enables both.

## Code Style

- Ruff with 120-character line limit
- Pre-commit hooks enforce formatting on every commit (`ruff check`, `ruff format`, pytest)
- Async everywhere: all DB calls use `async with get_db()`, all service methods are `async`
- UUID primary keys on all models; `TimestampMixin` provides `created_at`/`updated_at` on every table
