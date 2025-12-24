# VitAI Backend

Backend API service for VitAI - AI-powered nutritional analysis application that provides personalized health recommendations based on food product labels and ingredients.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nuxt 3 PWA   │◄──►│  FastAPI BE     │◄──►│  GPT-5.1 Chat   │
│   (Frontend)    │    │  (This Repo)    │    │  Multimodal     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   + Redis       │
                       └─────────────────┘
```

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Package Manager**: UV
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0+
- **Cache**: Redis 7+
- **AI Integration**: OpenAI GPT-5.1 Chat
- **Authentication**: API Key + JWT
- **Testing**: pytest
- **Linting**: Ruff

## Quick Start

### Option 1: Docker (Recommended for Quick Setup)

**Prerequisites**: Docker & Docker Compose, OpenAI API key

1. **Clone and setup**
   ```bash
   git clone git@github.com:ladsan1977/VitAI_backend.git
   cd vitai-backend
   cp .env.example .env
   ```

2. **Configure `.env`**
   ```env
   API_KEY=vitai_sk_prod_<run: python -c "import secrets; print(secrets.token_urlsafe(32))">
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start**
   ```bash
   docker-compose up -d
   ```

### Option 2: Local Development with Make

**Prerequisites**: Python 3.11+, [UV](https://docs.astral.sh/uv/), PostgreSQL, Redis, OpenAI API key

1. **Clone and setup**
   ```bash
   git clone git@github.com:ladsan1977/VitAI_backend.git
   cd vitai-backend
   cp .env.example .env
   ```

2. **Configure `.env`** (same as above)

3. **Install dependencies and run**
   ```bash
   make install  # Install dependencies with UV
   make run      # Start development server
   ```

### Access the API

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Making API Requests

All AI analysis endpoints require an API key:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_key_here" \
  -F "images=@product.jpg" \
  -F "analysis_type=complete"
```

For detailed API usage examples in different languages, see [docs/API_USAGE.md](docs/API_USAGE.md).

## Core Endpoints

- `GET /health` - Health check (no auth required)
- `GET /api/v1/ai/health` - AI service health check (no auth required)
- `POST /api/v1/ai/analyze` - Analyze nutrition from images (requires API key)

## Development

### Quick Make Commands

```bash
make install      # Install dependencies
make run          # Run development server
make test         # Run tests
make format       # Format code
make lint         # Check code quality
make check-all    # Run all checks (before commit)
```

For complete development guide, see **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**:
- Local development with UV
- Alternative setup methods
- Pre-commit hooks
- Testing strategies
- Project structure details

## Testing

```bash
# Run tests (requires UV installed)
uv run pytest

# Run with coverage
uv run pytest --cov=app
```

## Deployment

### Railway
1. Connect GitHub repository to Railway
2. Set environment variables
3. Deploy automatically on push to main

### Docker
```bash
docker build -t vitai-backend .
docker run -p 8000:8000 --env-file .env vitai-backend
```

## Security Features

- API Key Authentication
- Rate Limiting (20/min, 100/hour per key)
- Input Validation
- CORS Configuration
- Environment-based Secrets

## Project Structure

```
vitai-backend/
├── app/
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration
│   ├── api/             # API routes
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── tests/               # Tests
├── docs/                # Documentation
├── docker-compose.yml   # Docker setup
└── pyproject.toml       # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make check-all`
5. Submit a pull request

## Support

For issues and questions, create an issue in this repository.

---

**Note**: This backend works with the separate VitAI frontend repository.
