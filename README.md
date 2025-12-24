# VitAI Backend

Backend API service for VitAI - AI-powered nutritional analysis application that provides personalized health recommendations based on food product labels and ingredients.

## 🏗️ Architecture

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

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Package Manager**: UV (ultra-fast Python package installer)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0+
- **Cache**: Redis 7+
- **AI Integration**: OpenAI GPT-5.1 Chat (Responses API, Multimodal)
- **Authentication**: JWT with refresh tokens
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest
- **Linting & Formatting**: Ruff (replaces Black, isort, Flake8)
- **Containerization**: Docker + Docker Compose
- **Deployment**: Railway (planned)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (recommended) or pip
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installing UV (Recommended)

UV is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip (if you prefer)
pip install uv
```

### Local Development (Recommended)

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

   **Important:** Generate a secure API key for authentication:

   ```bash
   # Generate a secure API key
   python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"
   ```

   Copy the generated key and add it to your `.env` file:

   ```env
   API_KEY=vitai_sk_prod_<your_generated_key>
   OPEN_AI_KEY=your_openai_api_key
   ```

4. **Run the application locally**

   ```bash
   # Method 1: Using uv run (recommended)
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Method 2: Activate virtual environment manually
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**

   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

6. **Run tests (optional)**

   ```bash
   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=app
   ```

### Alternative: Docker Development

If you prefer containerized development or need to test the full production environment:

#### Quick Start with Docker

```bash
# Build and run in one command
docker build -t vitai-backend . && docker run -p 8000:8000 vitai-backend
```

#### Docker Compose (Full Stack)

```bash
# Start all services (API + Database + Redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Manual Docker Commands

```bash
# Build the image
docker build -t vitai-backend .

# Run the container
docker run -p 8000:8000 vitai-backend

# Run with environment variables
docker run -p 8000:8000 --env-file .env vitai-backend

# Run in development mode with volume mounting
docker run -p 8000:8000 -v $(pwd)/app:/app/app vitai-backend
```

## 🔐 API Authentication

### API Key Authentication

All AI analysis endpoints require API key authentication for security and rate limiting.

#### Setting Up Authentication

1. **Generate an API Key:**
   ```bash
   python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"
   ```

2. **Add to Environment:**
   ```env
   API_KEY=vitai_sk_prod_your_generated_key_here
   ```

3. **Using the API Key:**

   **With cURL:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/analyze" \
     -H "X-API-Key: vitai_sk_prod_your_key_here" \
     -F "images=@product.jpg" \
     -F "analysis_type=complete"
   ```

   **With Postman:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/v1/ai/analyze`
   - Headers tab:
     - Key: `X-API-Key`
     - Value: `vitai_sk_prod_your_key_here`
   - Body tab: `form-data`
     - Add your images and parameters

   **With Python:**
   ```python
   import requests

   headers = {
       "X-API-Key": "vitai_sk_prod_your_key_here"
   }

   files = {
       "images": open("product.jpg", "rb")
   }

   data = {
       "analysis_type": "complete"
   }

   response = requests.post(
       "http://localhost:8000/api/v1/ai/analyze",
       headers=headers,
       files=files,
       data=data
   )

   print(response.json())
   ```

   **With JavaScript/Fetch:**
   ```javascript
   const formData = new FormData();
   formData.append('images', fileInput.files[0]);
   formData.append('analysis_type', 'complete');

   const response = await fetch('http://localhost:8000/api/v1/ai/analyze', {
     method: 'POST',
     headers: {
       'X-API-Key': 'vitai_sk_prod_your_key_here'
     },
     body: formData
   });

   const data = await response.json();
   ```

### Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **20 requests per minute** per API key
- **100 requests per hour** per API key

Rate limit exceeded responses:
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "error": "too_many_requests"
}
```

Configure limits in `.env`:
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
```

### Authentication Errors

**Missing API Key (403):**
```json
{
  "detail": "API key is missing. Please provide an API key in the X-API-Key header."
}
```

**Invalid API Key (403):**
```json
{
  "detail": "Invalid API key. Please check your credentials."
}
```

## 📊 API Endpoints

### Core Endpoints

- `GET /health` - Health check (no auth required)
- `GET /api/v1/ai/health` - AI service health check (no auth required)

### AI Analysis (Authentication Required)

- `POST /api/v1/ai/analyze` - Analyze nutrition from product images (**requires API key**)

## 🧪 Testing

```bash
# Run all tests with UV
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_health.py

# Install development dependencies
uv sync --group dev
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before commits:

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run pre-commit on all files manually
uv run pre-commit run --all-files

# Run pre-commit on staged files
uv run pre-commit run
```

**What pre-commit does automatically:**

- ✅ **Code formatting** with Ruff
- ✅ **Linting** with automatic fixes
- ✅ **Test execution** to ensure functionality
- ✅ **File cleanup** (trailing whitespace, end-of-file fixes)
- ✅ **YAML validation**

**Note**: Pre-commit hooks will automatically run on every `git commit` and block the commit if any checks fail.

## 📦 UV Commands Reference

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

# Run a command in the virtual environment
uv run python script.py

# Show dependency tree
uv tree

# Lock dependencies (creates/updates uv.lock)
uv lock
```

## 🛠️ Make Commands

We provide convenient Make commands for common development tasks:

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

**💡 Tip**: Use `make check` during development and `make check-all` before commits for optimal workflow.

## 📦 Project Structure

```
vitai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration settings
│   ├── api/             # API routes
│   ├── core/            # Core functionality
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test files
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── pyproject.toml      # Project configuration & dependencies
├── uv.lock             # Dependency lock file (auto-generated)
└── .venv/              # Virtual environment (auto-created by UV)
```

## 🚀 Deployment

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

### Custom Server Deployment

1. Build Docker image: `docker build -t vitai-backend .`
2. Push to your registry or copy to server
3. Run with proper environment variables
4. Set up reverse proxy (nginx) for SSL termination

## 🔒 Security Features

- **API Key Authentication** - Secure header-based authentication
- **Rate Limiting** - 20 requests/minute, 100 requests/hour per API key
- **Input Validation** - Comprehensive request data validation and sanitization
- **CORS Configuration** - Configured for secure frontend integration
- **Environment-based Configuration** - Secrets managed via environment variables
- **Secure Key Generation** - Cryptographically secure API key generation
- **Future JWT Support** - Architecture ready for user-based authentication

## 📈 Monitoring & Observability

- Health check endpoints
- Structured logging
- Performance metrics
- Error tracking and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

[Your License Here]

## 🆘 Support

For support and questions:

- Create an issue in this repository
- Contact: [your-email@domain.com]

---

**Note**: This backend is designed to work with the separate VitAI frontend repository. The frontend will consume these APIs for the complete nutritional analysis experience.
