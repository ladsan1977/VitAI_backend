"""Base models for the application."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = False
    error_code: str | None = None
    details: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "ok"
    env: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
