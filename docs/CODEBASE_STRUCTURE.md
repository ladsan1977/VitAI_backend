# VitAI Backend - Codebase Structure

## Overview

VitAI Backend is a **FastAPI-based API service** for AI-powered nutritional analysis. It leverages OpenAI's GPT-5.1 Chat multimodal model to analyze food product images and provide personalized nutritional insights.

- **Version**: 0.1.0 (Alpha)
- **Python Version**: 3.11+
- **Framework**: FastAPI

---

## Project Directory Structure

```
vitai-backend/
├── app/                              # Core application code
│   ├── api/                          # HTTP interface layer (thin routes, no business logic)
│   │   └── v1/                       # Versioned API endpoints
│   │       ├── ai.py                 # AI analysis endpoints (/ai/analyze, /ai/health)
│   │       └── analytics.py          # Analytics endpoints (/analytics/metrics, /analytics/costs)
│   │
│   ├── controllers/                  # Business logic orchestration layer
│   │   ├── analysis_controller.py    # Product analysis workflow (dedup, cache, OpenAI, persistence)
│   │   ├── analytics_controller.py   # AI consumption metrics, cost analysis, performance reporting
│   │   └── prompt_controller.py      # Prompt version management (CRUD, activation, multi-language)
│   │
│   ├── core/                         # Cross-cutting framework concerns
│   │   ├── exceptions.py             # Custom exception hierarchy (VitAIException base)
│   │   ├── rate_limit.py             # Rate limiting configuration (slowapi)
│   │   └── security.py               # API key authentication with timing-safe comparison
│   │
│   ├── db/                           # Database layer (PostgreSQL + SQLAlchemy 2.0 async)
│   │   ├── models/                   # ORM models (SQLAlchemy declarative)
│   │   │   ├── analysis.py           # Analysis model - product analyses with JSONB results
│   │   │   ├── ai_consumption_metric.py  # AI consumption metrics - costs, tokens, response times
│   │   │   └── prompt_version.py     # Prompt versions - versioned templates with activation control
│   │   ├── repositories/             # Data access layer (pure CRUD, no business logic)
│   │   │   ├── base.py               # BaseRepository - generic CRUD operations (create, get, update, delete)
│   │   │   ├── analysis.py           # AnalysisRepository - image hash lookup, session history
│   │   │   ├── ai_consumption_metric.py  # AiConsumptionMetricsRepository - cost/performance aggregations
│   │   │   └── prompt_version.py     # PromptVersionRepository - active prompt retrieval, version activation
│   │   ├── base.py                   # SQLAlchemy Base class and TimestampMixin (created_at, updated_at)
│   │   └── session.py                # Async engine, session factory, and get_db() dependency
│   │
│   ├── middleware/                    # Request/response processing pipeline
│   │   └── metrics_middleware.py      # Session ID management (cookies) and request timing/logging
│   │
│   ├── models/                       # Pydantic data models (request/response schemas)
│   │   └── ai.py                     # AIAnalysisResponse, ProductInfo, NutritionalInfo, HealthAnalysis
│   │
│   ├── services/                     # External service integrations
│   │   ├── prompts/                  # AI prompt templates (markdown files, multi-language)
│   │   ├── image_service.py          # Image processing, base64 encoding, optimization
│   │   ├── openai_service.py         # OpenAI API integration, multimodal analysis
│   │   └── redis_service.py          # Redis cache integration for API response caching
│   │
│   ├── utils/                        # Shared utility functions
│   │   └── validators.py             # Input validation helpers (images, request data)
│   │
│   ├── config.py                     # Settings (Pydantic BaseSettings) - DB, Redis, OpenAI, security
│   └── main.py                       # FastAPI app entry point, middleware stack, lifecycle events
│
├── alembic/                          # Database migrations (Alembic + async SQLAlchemy)
│   ├── versions/                     # Migration scripts (chronological schema changes)
│   │   ├── cd9e66b6a9ce_initial_schema_...py  # Initial: analyses, ai_consumption_metrics, prompt_versions
│   │   └── ...                       # Subsequent schema modifications
│   └── env.py                        # Alembic config for async PostgreSQL via asyncpg
│
├── tests/                            # Test suite (pytest)
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_health.py                # Health endpoint tests
│   └── test_ai_endpoint.py           # AI analysis endpoint tests
│
├── docs/                             # Project documentation
│   ├── API_USAGE.md                  # API usage examples (cURL, Python, JS, Go)
│   ├── CODEBASE_STRUCTURE.md         # This file - architecture and code reference
│   ├── DEPLOYMENT.md                 # Render deployment guide
│   └── DEVELOPMENT.md               # Local development setup
│
├── scripts/                          # Utility scripts
├── .github/workflows/                # CI/CD workflows
│
├── Dockerfile                        # Docker image definition (Python 3.11-slim + UV)
├── docker-compose.yml                # Multi-service stack (PostgreSQL + Redis + API)
├── alembic.ini                       # Alembic migration configuration
├── render.yaml                       # Render deployment infrastructure-as-code
├── pyproject.toml                    # Python project config (dependencies, Ruff, pytest)
├── Makefile                          # Development commands (install, test, lint, format)
├── .env.example                      # Environment variables template (no real credentials)
├── .pre-commit-config.yaml           # Pre-commit hooks for code quality
└── README.md                         # Project overview
```

---

## Documentation Files (.md)

### Primary Documentation

| File | Purpose |
|------|---------|
| [README.md](../README.md) | Project overview, architecture diagram, quick start guides, deployment overview |
| [docs/DEVELOPMENT.md](DEVELOPMENT.md) | Development setup, testing, code quality tools, Make commands, debugging |
| [docs/DEPLOYMENT.md](DEPLOYMENT.md) | Render platform deployment, environment configuration, troubleshooting |
| [docs/API_USAGE.md](API_USAGE.md) | Authentication, rate limiting, multi-language code examples (cURL, Python, JS, Go) |

### Additional Markdown Files

- **Prompt Templates** in `app/services/prompts/`: Markdown files containing structured prompts for nutritional analysis AI queries (multi-language support)

---

## Application Architecture

### Layered Architecture

```
Request → Middleware (session, timing, logging)
    ↓
Routes (HTTP validation, thin handlers)
    ↓
Controllers (business logic orchestration)
    ↓
Services + Repositories (external APIs + data access)
    ↓
Database / OpenAI / Redis
    ↓
Response ← Middleware (cookies, timing headers)
```

### Entry Point

**`app/main.py`** - FastAPI application with:
- Security middleware stack (headers, HTTPS redirect, trusted hosts, CORS)
- Metrics middleware (session management, request timing)
- Rate limiting exception handler
- API router mounting (AI + Analytics)
- Database and Redis lifecycle management (startup/shutdown)
- Health check with service status (database + Redis)

### API Layer (`app/api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Base health check (database + Redis status) |
| `/api/v1/ai/analyze` | POST | Multi-image nutritional analysis (with DB deduplication) |
| `/api/v1/ai/health` | GET | AI service health status |
| `/api/v1/ai/cache/stats` | GET | Redis cache statistics |
| `/api/v1/analytics/metrics` | GET | AI consumption metrics summary |
| `/api/v1/analytics/costs` | GET | OpenAI cost breakdown with projections |
| `/api/v1/analytics/performance` | GET | Performance metrics with cache efficiency |
| `/api/v1/analytics/history` | GET | Analysis history for current session |
| `/api/v1/analytics/history/{id}` | GET | Full analysis details by ID |

### Controller Layer (`app/controllers/`)

| Controller | Responsibility |
|------------|----------------|
| `analysis_controller.py` | Full analysis workflow: image hashing, DB deduplication, OpenAI call, cost calculation, persistence, prompt loading with TTL cache |
| `analytics_controller.py` | Metrics aggregation: cache hit rates, OpenAI costs, response times, token usage, cost projections |
| `prompt_controller.py` | Prompt version management: create, activate, deactivate, list, multi-language support |

### Core Layer (`app/core/`)

| Module | Responsibility |
|--------|----------------|
| `security.py` | API key authentication with timing-safe comparison |
| `rate_limit.py` | Per-key/IP rate limiting (slowapi) |
| `exceptions.py` | Custom exception hierarchy |

### Database Layer (`app/db/`)

| Component | Responsibility |
|-----------|----------------|
| `base.py` | SQLAlchemy declarative base + `TimestampMixin` (auto `created_at`/`updated_at`) |
| `session.py` | Async engine with connection pooling, `AsyncSessionLocal` factory, `get_db()` dependency |
| `models/` | ORM models: `Analysis`, `AiConsumptionMetric`, `PromptVersion` (UUID PKs, JSONB, indexes) |
| `repositories/` | Data access: `BaseRepository` (generic CRUD) + specialized repos per model |

### Service Layer (`app/services/`)

| Service | Responsibility |
|---------|----------------|
| `openai_service.py` | OpenAI API integration, prompt loading, multimodal analysis |
| `image_service.py` | File upload processing, base64 encoding, image optimization |
| `redis_service.py` | Redis cache connection, API response caching, cache statistics |

### Middleware Layer (`app/middleware/`)

| Middleware | Responsibility |
|------------|----------------|
| `metrics_middleware.py` | Session ID generation (UUID v4 cookies), request/response timing, `X-Response-Time` header, request logging |

### Models (`app/models/`)

Pydantic models for request/response validation:
- `AIAnalysisResponse` - Main API response wrapper
- `ProductInfo` - Product identification
- `NutritionalInfo` - Nutritional facts extraction
- `IngredientsInfo` - Ingredient analysis with allergens
- `HealthAnalysis` - Health scoring and recommendations

### Configuration (`app/config.py`)

Pydantic BaseSettings for environment-based configuration:
- OpenAI API settings (model: `gpt-5.1-chat-latest`)
- Database settings (PostgreSQL URL, pool size, max overflow)
- Redis settings (connection URL, cache TTL)
- File upload constraints (10MB max, JPEG/PNG/WebP)
- Security configuration (API key validation)
- Rate limiting settings (20/min, 100/hour default)
- CORS origins management
- Analytics feature flag

---

## Database Schema

Three PostgreSQL tables with UUID primary keys and automatic timestamps:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `analyses` | Stores product analysis results | `image_hash` (unique, dedup), `session_id`, `analysis_result` (JSONB), `analysis_type` |
| `ai_consumption_metrics` | Tracks AI API usage and costs | `session_id`, `cache_hit`, `response_time_ms`, `openai_cost_usd`, `tokens_used`, `prompt_tokens`, `completion_tokens` |
| `prompt_versions` | Versioned prompt templates | `version`, `language`, `content`, `active` (one active per language) |

Migrations managed by **Alembic** with async SQLAlchemy support via **asyncpg** driver.

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, dev tools, Ruff/pytest config |
| `Dockerfile` | Python 3.11-slim with UV package manager |
| `docker-compose.yml` | PostgreSQL + Redis + API (env vars via `${VARIABLE}` substitution) |
| `alembic.ini` | Alembic migration configuration |
| `render.yaml` | Render deployment infrastructure-as-code |
| `Makefile` | Development commands (install, test, lint, format) |
| `.pre-commit-config.yaml` | Git hooks for code quality |
| `.env.example` | Environment variables template (no real credentials) |

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI 0.104.0+ |
| **Server** | Uvicorn 0.24.0+ |
| **Package Manager** | UV (Rust-based) |
| **AI Integration** | OpenAI API (GPT-5.1 Chat) |
| **Database** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy 2.0+ (async with asyncpg) |
| **Migrations** | Alembic 1.12+ |
| **Cache** | Redis 7+ |
| **Image Processing** | Pillow |
| **Rate Limiting** | slowapi |
| **Testing** | pytest with coverage |
| **Code Quality** | Ruff (linting + formatting) |
| **Deployment** | Docker, Render |

---

## Development Patterns

### Architecture Patterns
- **Layered Architecture**: Routes → Controllers → Services/Repositories → Database
- **Repository Pattern**: Data access abstraction with generic base CRUD
- **Controller Pattern**: Business logic orchestration (separate from routes and data access)
- **Async/Await**: All I/O operations are async (database, HTTP, Redis)
- **Dependency Injection**: FastAPI `Depends()` for database sessions and authentication
- **Anonymous-First Design**: Session-based tracking via cookies without user accounts

### Security Patterns
- API key format validation (`vitai_sk_prod_<random>`)
- Timing-safe string comparison (`secrets.compare_digest`)
- Masked logging (first 8 + last 4 characters)
- Explicit CORS origins (no wildcards)
- Environment variable substitution in Docker (no hardcoded credentials)
- HttpOnly session cookies (Secure flag in production)

### Code Quality
- **Ruff**: Linting + formatting (120-char line length)
- **pytest**: Testing with coverage tracking
- **Pre-commit hooks**: Automated quality checks

---

## Make Commands

```bash
make install      # Install dependencies with UV
make dev          # Install dev dependencies
make format       # Format code with Ruff
make lint         # Check code quality
make test         # Run pytest suite
make test-cov     # Run with coverage report
make check-all    # Lint + tests (pre-commit)
make run          # Start dev server with reload
make clean        # Clean cache files
```

---

## Database Commands

```bash
# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

---

## API Authentication

All protected endpoints require the `X-API-Key` header:

```bash
curl -X POST "https://your-api.onrender.com/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_api_key" \
  -F "images=@food_label.jpg"
```

---

## Related Documentation

- [Development Guide](DEVELOPMENT.md) - Setup, testing, debugging
- [Deployment Guide](DEPLOYMENT.md) - Render deployment instructions
- [API Usage Guide](API_USAGE.md) - Multi-language examples
