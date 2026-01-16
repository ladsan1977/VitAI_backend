import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .api.v1.ai import router as ai_router
from .config import settings
from .core.rate_limit import limiter
from .services.redis_service import redis_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VitAI Backend API",
    description="AI-powered nutritional analysis application with API key authentication",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    openapi_url="/openapi.json" if settings.app_env != "production" else None,
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


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Remove server header if present
    if "server" in response.headers:
        del response.headers["server"]
    return response


# HTTPS redirect middleware (production only)
if settings.https_only and settings.app_env == "production":

    @app.middleware("http")
    async def https_redirect(request: Request, call_next):
        """Redirect HTTP requests to HTTPS in production."""
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "http":
            url = request.url.replace(scheme="https")
            return JSONResponse(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": str(url)})
        return await call_next(request)


# Trusted Host Middleware (production only)
if settings.app_env == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
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
async def health():
    """Health check endpoint for monitoring and Render."""
    redis_health = await redis_service.health_check()
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": settings.version,
        "services": {
            "redis": redis_health,
        },
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup information and initialize services."""
    logger.info(f"Starting VitAI Backend v{settings.version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"HTTPS Only: {settings.https_only}")
    logger.info(f"Rate Limiting: {settings.rate_limit_enabled}")

    # Initialize Redis connection
    redis_connected = await redis_service.connect()
    logger.info(f"Redis Cache: {'enabled' if redis_connected else 'disabled/unavailable'}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown and cleanup resources."""
    logger.info("Shutting down VitAI Backend")

    # Close Redis connection
    await redis_service.disconnect()
