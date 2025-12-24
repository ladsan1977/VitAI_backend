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
                       │  (Phase 2)      │
                       └─────────────────┘
```

**Current:** Stateless API - only calls OpenAI (no database required for deployment)
**Phase 2:** Will add PostgreSQL for data persistence and Redis for distributed caching

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Package Manager**: UV
- **AI Integration**: OpenAI GPT-5.1 Chat (Multimodal)
- **Authentication**: API Key (X-API-Key header)
- **Rate Limiting**: slowapi (in-memory)
- **Testing**: pytest with coverage
- **Linting**: Ruff
- **Deployment**: Render (free tier), Docker-ready
- **Database**: PostgreSQL 15+ (optional - not currently used)
- **Cache**: Redis 7+ (optional - not currently used)

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

### Render (Recommended - FREE Tier)

**Quick Deploy:**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Create account at [render.com](https://render.com) (free)
2. New Web Service → Connect repository
3. Select **Docker** runtime, **Free** tier
4. Set environment variables:
   - `OPEN_AI_KEY` - Your OpenAI API key
   - `API_KEY` - Generate: `python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"`
   - `CORS_ORIGINS` - `["https://your-frontend.com"]`
5. Deploy!

**Features:**
- ✅ $0/month (free tier - 750 hours/month)
- ✅ Auto HTTPS/SSL
- ✅ GitHub auto-deploy
- ✅ No database setup needed
- ⚠️ Sleeps after 15min inactivity (15-30s cold start)

For detailed deployment guide, see **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

### Docker (Alternative)

```bash
docker build -t vitai-backend .
docker run -p 8000:8000 --env-file .env vitai-backend
```

## Security Features

- **API Key Authentication** - X-API-Key header with format validation
- **Rate Limiting** - 10/min, 100/hour per key (production), 20/min dev
- **HTTPS Enforcement** - Automatic redirect in production
- **Security Headers** - HSTS, X-Frame-Options, X-XSS-Protection, nosniff
- **CORS Protection** - Explicit origin whitelist (no wildcards)
- **Input Validation** - File type/size limits, content verification
- **Trusted Hosts** - Protection against host header attacks
- **Environment Secrets** - Secure configuration management
- **Timing-Safe Comparison** - API key validation resistant to timing attacks

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
