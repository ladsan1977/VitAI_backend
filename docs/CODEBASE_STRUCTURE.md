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
├── app/                          # Core application code
│   ├── api/v1/                   # API endpoints (versioned)
│   │   ├── __init__.py
│   │   └── ai.py                 # AI analysis endpoints
│   ├── core/                     # Core functionality
│   │   ├── exceptions.py         # Custom exception classes
│   │   ├── rate_limit.py         # Rate limiting logic
│   │   └── security.py           # Authentication & authorization
│   ├── models/                   # Pydantic data models
│   │   └── ai.py                 # Request/response models
│   ├── services/                 # Business logic layer
│   │   ├── prompts/              # AI prompt templates (markdown)
│   │   ├── image_service.py      # Image processing
│   │   └── openai_service.py     # OpenAI API integration
│   ├── utils/                    # Utility functions
│   │   └── validators.py         # Input validation helpers
│   ├── config.py                 # Settings (Pydantic BaseSettings)
│   └── main.py                   # FastAPI application entry point
│
├── tests/                        # Test suite (pytest)
│   ├── conftest.py               # Pytest fixtures
│   ├── test_health.py            # Health endpoint tests
│   └── test_ai_endpoint.py       # AI analysis endpoint tests
│
├── docs/                         # Documentation
│   ├── API_USAGE.md              # API usage examples
│   ├── DEPLOYMENT.md             # Render deployment guide
│   └── DEVELOPMENT.md            # Local development setup
│
├── scripts/                      # Utility scripts
├── .github/workflows/            # CI/CD workflows
│
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Multi-service development setup
├── render.yaml                   # Render deployment config
├── pyproject.toml                # Python project configuration
├── Makefile                      # Development commands
├── .env.example                  # Environment variables template
├── .pre-commit-config.yaml       # Pre-commit hooks
└── README.md                     # Project overview
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

- **Prompt Templates** in `app/services/prompts/`: Markdown files containing structured prompts for nutritional analysis AI queries

---

## Application Architecture

### Entry Point

**`app/main.py`** - FastAPI application with:
- Security middleware stack (headers, HTTPS redirect, trusted hosts, CORS)
- Rate limiting exception handler
- API router mounting

### API Layer (`app/api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Base health check |
| `/api/v1/ai/analyze` | POST | Multi-image nutritional analysis |
| `/api/v1/ai/health` | GET | AI service health status |

### Core Layer (`app/core/`)

| Module | Responsibility |
|--------|----------------|
| `security.py` | API key authentication with timing-safe comparison |
| `rate_limit.py` | Per-key/IP rate limiting (slowapi) |
| `exceptions.py` | Custom exception hierarchy |

### Service Layer (`app/services/`)

| Service | Responsibility |
|---------|----------------|
| `openai_service.py` | OpenAI API integration, prompt loading, multimodal analysis |
| `image_service.py` | File upload processing, base64 encoding, image optimization |

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
- File upload constraints (10MB max, JPEG/PNG/WebP)
- Security configuration (API key validation)
- Rate limiting settings (20/min, 100/hour default)
- CORS origins management

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, dev tools, Ruff/pytest config |
| `Dockerfile` | Python 3.11-slim with UV package manager |
| `docker-compose.yml` | PostgreSQL + Redis + API service stack |
| `render.yaml` | Render deployment infrastructure-as-code |
| `Makefile` | Development commands (install, test, lint, format) |
| `.pre-commit-config.yaml` | Git hooks for code quality |
| `.env.example` | Environment variables template |

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI 0.104.0+ |
| **Server** | Uvicorn 0.24.0+ |
| **Package Manager** | UV (Rust-based) |
| **AI Integration** | OpenAI API (GPT-5.1 Chat) |
| **Database** | PostgreSQL 15+ (optional) |
| **Cache** | Redis 7+ (optional) |
| **Image Processing** | Pillow |
| **Rate Limiting** | slowapi |
| **Testing** | pytest with coverage |
| **Code Quality** | Ruff (linting + formatting) |
| **Deployment** | Docker, Render |

---

## Development Patterns

### Architecture Patterns
- **Layered Architecture**: Routes → Services → Utils
- **Async/Await**: All I/O operations are async
- **Dependency Injection**: FastAPI `Depends()` for middleware

### Security Patterns
- API key format validation (`vitai_sk_prod_<random>`)
- Timing-safe string comparison (`secrets.compare_digest`)
- Masked logging (first 8 + last 4 characters)
- Explicit CORS origins (no wildcards)

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
