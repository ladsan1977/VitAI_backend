# Development Guide

This guide covers local development setup, testing, and advanced development workflows for the VitAI Backend.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Alternative Setup Methods](#alternative-setup-methods)
- [UV Package Manager](#uv-package-manager)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Make Commands](#make-commands)
- [Project Structure](#project-structure)
- [Docker Development](#docker-development)

## Local Development Setup

For local development without Docker, using UV for fast dependency management.

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) package manager
- PostgreSQL 15+ (running locally)
- Redis 7+ (running locally)

### Installing UV

UV is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip (if you prefer)
pip install uv
```

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone git@github.com:ladsan1977/VitAI_backend.git
   cd vitai-backend
   ```

2. **Install dependencies with UV**
   ```bash
   # Install all dependencies (production + development)
   uv sync

   # Verify installation
   uv tree
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Generate a secure API key:
   ```bash
   python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"
   ```

   Update your `.env`:
   ```env
   API_KEY=vitai_sk_prod_<your_generated_key>
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=postgresql://user:pass@localhost:5432/vitai
   REDIS_URL=redis://localhost:6379
   ```

4. **Run the application**
   ```bash
   # Method 1: Using uv run (recommended)
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Method 2: Activate virtual environment manually
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Alternative Setup Methods

### Using Docker Compose (Recommended for Quick Start)

See the main [README.md](../README.md) for Docker Compose setup.

### Using Docker (Single Container)

```bash
# Build and run in one command
docker build -t vitai-backend . && docker run -p 8000:8000 vitai-backend

# Or step by step
docker build -t vitai-backend .
docker run -p 8000:8000 --env-file .env vitai-backend

# With volume mounting for development
docker run -p 8000:8000 -v $(pwd)/app:/app/app vitai-backend
```

### Using Traditional pip

If you prefer not to use UV:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run application
uvicorn app.main:app --reload
```

## UV Package Manager

### Common UV Commands

```bash
# Install all dependencies (including dev)
uv sync

# Install only production dependencies
uv sync --no-dev

# Add a new dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Update a specific package
uv add --upgrade package-name

# Run a command in the virtual environment
uv run python script.py
uv run pytest
uv run uvicorn app.main:app --reload

# Show dependency tree
uv tree

# Lock dependencies (creates/updates uv.lock)
uv lock

# Export requirements.txt
uv pip compile pyproject.toml -o requirements.txt
```

### Why UV?

- **10-100x faster** than pip
- **Deterministic** dependency resolution
- **Compatible** with pip and existing tools
- **Modern** resolver that handles complex dependencies
- **Built-in** virtual environment management

## Testing

### Running Tests

```bash
# Run all tests with UV
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run with detailed output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_health.py

# Run specific test
uv run pytest tests/test_health.py::test_health_endpoint

# Run tests in parallel
uv run pytest -n auto
```

### Writing Tests

Place tests in the `tests/` directory:

```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test Coverage

```bash
# Generate coverage report
uv run pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

## Code Quality

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before commits.

#### Setup

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files

# Run on staged files only
uv run pre-commit run
```

#### What Pre-commit Does

- ✅ Code formatting with Ruff
- ✅ Linting with automatic fixes
- ✅ Test execution
- ✅ File cleanup (trailing whitespace, end-of-file fixes)
- ✅ YAML validation

**Note**: Pre-commit hooks automatically run on every `git commit` and block the commit if checks fail.

### Ruff Linting & Formatting

```bash
# Lint code (check only)
uv run ruff check .

# Lint with automatic fixes
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .
```

### Configuration

Ruff is configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = []
```

## Make Commands

Convenient commands for common development tasks.

### Development Setup

```bash
# Install dependencies
make install

# Install development dependencies
make dev
```

### Code Quality & Testing

```bash
# Quick check (lint + basic tests)
make check

# Complete verification (lint + all tests)
make check-all

# Lint code (without fixing)
make lint

# Format code automatically
make format

# Run tests
make test

# Run tests with coverage
make test-cov
```

### Development Server

```bash
# Run development server with auto-reload
make run
```

### Maintenance

```bash
# Clean cache files and temporary directories
make clean
```

### Pre-commit Workflow

```bash
# Before committing, run this to ensure code quality
make check-all
```

**Tip**: Use `make check` during development and `make check-all` before commits.

## Project Structure

```
vitai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   │
│   ├── api/                 # API routes and endpoints
│   │   ├── __init__.py
│   │   └── v1/              # API version 1
│   │       ├── __init__.py
│   │       ├── ai.py        # AI analysis endpoints
│   │       └── health.py    # Health check endpoints
│   │
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py      # Authentication & security
│   │   └── rate_limit.py    # Rate limiting
│   │
│   ├── models/              # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   └── user.py
│   │
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── ai_service.py    # AI analysis service
│   │
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── logger.py
│
├── tests/                   # Test files
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration & fixtures
│   ├── test_health.py
│   └── test_ai.py
│
├── docs/                    # Documentation
│   ├── API_USAGE.md
│   └── DEVELOPMENT.md
│
├── .github/                 # GitHub workflows
│   └── workflows/
│
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── pyproject.toml          # Project configuration & dependencies
├── uv.lock                 # Dependency lock file (auto-generated)
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── Makefile                # Make commands
└── README.md               # Main documentation
```

### Key Files Explained

- **`app/main.py`**: FastAPI application instance and middleware setup
- **`app/config.py`**: Environment-based configuration using Pydantic
- **`app/api/v1/`**: API endpoints organized by version
- **`app/core/`**: Core functionality like auth, rate limiting
- **`app/services/`**: Business logic separated from routes
- **`pyproject.toml`**: All project metadata, dependencies, and tool configurations
- **`uv.lock`**: Lock file ensuring reproducible builds
- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration

## Docker Development

### Docker Compose Services

The `docker-compose.yml` defines:

- **api**: FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis cache

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v

# Rebuild containers
docker-compose up -d --build

# Execute commands in running container
docker-compose exec api bash
docker-compose exec postgres psql -U postgres

# Scale services
docker-compose up -d --scale api=3
```

### Development with Docker

```bash
# Run with live code reloading
docker-compose up -d

# The volume mount in docker-compose.yml ensures changes are reflected:
# volumes:
#   - ./app:/app/app

# Rebuild after dependency changes
docker-compose down
docker-compose up -d --build
```

## Environment Variables

### Required Variables

```env
# API Configuration
API_KEY=vitai_sk_prod_your_secure_key_here
OPENAI_API_KEY=sk-your_openai_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/vitai

# Redis
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true
```

### Optional Variables

```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Debugging

### Using Python Debugger

Add breakpoints in your code:

```python
import pdb; pdb.set_trace()
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### Logging

Configure logging in `app/utils/logger.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

Use in your code:

```python
from app.utils.logger import logger

logger.info("Processing request")
logger.error("Error occurred", exc_info=True)
```

## Database Migrations

When you add database models, create migrations:

```bash
# Initialize Alembic (first time only)
uv run alembic init alembic

# Create a migration
uv run alembic revision --autogenerate -m "Add user table"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Tips & Best Practices

1. **Use UV for speed**: UV is significantly faster than pip for installation and updates.

2. **Run tests frequently**: Use `make check` during development to catch issues early.

3. **Pre-commit hooks**: Always run `uv run pre-commit run --all-files` before pushing.

4. **Environment variables**: Never commit `.env` files. Always use `.env.example` as a template.

5. **Docker for consistency**: Use Docker Compose to ensure all developers have the same environment.

6. **Keep dependencies updated**: Regularly run `uv sync --upgrade` to update dependencies.

7. **Write tests first**: Follow TDD principles when adding new features.

8. **Use type hints**: FastAPI and Pydantic work best with proper type annotations.

9. **Document your code**: Add docstrings to functions and classes.

10. **Monitor logs**: Use structured logging to make debugging easier.

## Getting Help

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **UV Docs**: https://docs.astral.sh/uv/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pytest Docs**: https://docs.pytest.org/

For project-specific issues, create an issue in the repository.
