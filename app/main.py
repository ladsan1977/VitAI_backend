from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .api.v1.ai import router as ai_router
from .config import settings
from .core.rate_limit import limiter

app = FastAPI(
    title="VitAI Backend API",
    description="AI-powered nutritional analysis application with API key authentication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "AI Analysis",
            "description": "AI-powered nutritional analysis endpoints (requires API key)",
        },
    ],
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

# Add rate limiting state to the app
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "error": "too_many_requests",
        },
    )


# Include API routers
app.include_router(ai_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}
