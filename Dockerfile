FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (opcional, útil para futuras libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy Python dependency files and README (required by hatchling)
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies
RUN uv sync --frozen --no-cache --no-dev

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Run the application using uv
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
