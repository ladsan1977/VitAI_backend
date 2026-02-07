"""Middleware for cross-cutting concerns."""

from .metrics_middleware import MetricsMiddleware

__all__ = ["MetricsMiddleware"]
