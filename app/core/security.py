"""Security utilities for API authentication."""

import logging
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from ..config import settings

logger = logging.getLogger(__name__)

# Define the API Key header security scheme
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


def mask_api_key(key: str) -> str:
    """
    Mask API key for logging (show first 8 and last 4 chars).

    Args:
        key: The API key to mask

    Returns:
        str: Masked API key for safe logging
    """
    if not key or len(key) < 13:
        return "****"
    return f"{key[:8]}****{key[-4:]}"


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate API key follows the expected format.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if format is valid, False otherwise
    """
    if not api_key:
        return False
    if not api_key.startswith("vitai_sk_prod_"):
        return False
    if len(api_key) < 30:  # Minimum length check
        return False
    return True


async def verify_api_key(api_key: Annotated[str | None, Depends(api_key_header)] = None) -> str:
    """
    Verify the API key from the request header.

    Args:
        api_key: The API key from the request header

    Returns:
        str: The validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    logger.debug("verify_api_key called")

    if api_key is None:
        logger.warning(f"API key missing. Expected header: {settings.api_key_header}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is missing. Please provide an API key in the X-API-Key header.",
        )

    logger.debug(f"API key received: {mask_api_key(api_key)}")

    # Validate API key format first (prevents brute force attacks)
    if not validate_api_key_format(api_key):
        logger.warning(f"Invalid API key format: {mask_api_key(api_key)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key format.",
        )

    # Log configured API key status
    configured_key_status = "set" if settings.api_key else "empty/not configured"
    configured_key_masked = mask_api_key(settings.api_key) if settings.api_key else "****"
    logger.debug(f"Configured API_KEY status: {configured_key_status} ({configured_key_masked})")

    # Validate the API key against the configured key (timing-safe comparison)
    if not secrets.compare_digest(api_key, settings.api_key):
        logger.warning("API key validation failed - provided key does not match configured API_KEY")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key. Please check your credentials.",
        )

    logger.debug("API key validated successfully")
    return api_key


def generate_api_key(prefix: str = "vitai_sk_prod") -> str:
    """
    Generate a secure API key.

    Args:
        prefix: The prefix for the API key (default: "vitai_sk_prod")

    Returns:
        str: A securely generated API key

    Example:
        >>> key = generate_api_key()
        >>> print(key)
        vitai_sk_prod_abc123xyz...
    """
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"
