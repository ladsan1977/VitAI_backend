"""Rate limiting configuration for API endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import settings


def get_api_key_identifier(request) -> str:
    """
    Get the identifier for rate limiting based on API key or IP address.

    Args:
        request: The FastAPI request object

    Returns:
        str: The API key from headers or the remote IP address
    """
    # Try to get the API key from headers
    api_key = request.headers.get(settings.api_key_header)
    if api_key:
        return api_key

    # Fallback to IP address if no API key is provided
    return get_remote_address(request)


# Initialize the rate limiter
limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=[],  # No default limits, we'll set them per-endpoint
    enabled=settings.rate_limit_enabled,
)
