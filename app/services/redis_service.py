"""Redis caching service with circuit breaker pattern for graceful degradation."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from ..config import settings
from ..models.ai import AIAnalysisResponse

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Simple circuit breaker implementation for Redis operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds to wait before trying half-open state.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED

    def record_success(self) -> None:
        """Record a successful operation and reset failure count."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed operation and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_execute(self) -> bool:
        """Check if operation can proceed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now(UTC) - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False

        # HALF_OPEN - allow one request to test recovery
        return True


class RedisService:
    """Service for Redis caching operations with circuit breaker pattern."""

    CACHE_PREFIX = "vitai:cache:v1"

    def __init__(self):
        """Initialize Redis service."""
        self._pool: ConnectionPool | None = None
        self._client: redis.Redis | None = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.redis_circuit_breaker_threshold,
            recovery_timeout=settings.redis_circuit_breaker_timeout,
        )
        self._connected = False

    async def connect(self) -> bool:
        """Establish Redis connection with pooling.

        Returns:
            True if connection successful, False otherwise.
        """
        if not settings.redis_enabled:
            logger.info("Redis caching is disabled via configuration")
            return False

        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_timeout,
                decode_responses=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection with ping
            await self._client.ping()
            self._connected = True
            logger.info(f"Redis connected successfully to {settings.redis_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup resources."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()
        self._connected = False
        logger.info("Redis connection closed")

    async def health_check(self) -> dict[str, Any]:
        """Check Redis connection health.

        Returns:
            Dictionary with health status information.
        """
        if not settings.redis_enabled:
            return {"status": "disabled", "enabled": False}

        if not self._connected or not self._client:
            return {
                "status": "disconnected",
                "enabled": True,
                "circuit_state": self._circuit_breaker.state.value,
            }

        try:
            await self._client.ping()
            info = await self._client.info("memory")
            return {
                "status": "healthy",
                "enabled": True,
                "circuit_state": self._circuit_breaker.state.value,
                "used_memory": info.get("used_memory_human", "unknown"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "enabled": True,
                "error": str(e),
                "circuit_state": self._circuit_breaker.state.value,
            }

    @staticmethod
    def _generate_cache_key(
        images: list[tuple[str, str, str]],
        analysis_type: str,
        user_profile: dict[str, Any] | None = None,
        dietary_preferences: list[str] | None = None,
        health_conditions: list[str] | None = None,
    ) -> str:
        """Generate a deterministic cache key based on input parameters.

        Args:
            images: List of (base64_data, content_type, filename) tuples.
            analysis_type: Type of analysis ("complete", "nutrition", "ingredients").
            user_profile: Optional user profile dictionary.
            dietary_preferences: Optional list of dietary preferences.
            health_conditions: Optional list of health conditions.

        Returns:
            Cache key string in format: vitai:cache:v1:{content_hash}:{analysis_type}:{profile_hash}
        """
        # Hash image content (concatenate base64 data)
        image_data = "".join(img[0] for img in images)
        content_hash = hashlib.sha256(image_data.encode()).hexdigest()[:16]

        # Hash profile parameters (sorted for determinism)
        profile_parts = []
        if user_profile:
            profile_parts.append(json.dumps(user_profile, sort_keys=True))
        if dietary_preferences:
            profile_parts.append(",".join(sorted(dietary_preferences)))
        if health_conditions:
            profile_parts.append(",".join(sorted(health_conditions)))

        if profile_parts:
            profile_str = "|".join(profile_parts)
            profile_hash = hashlib.sha256(profile_str.encode()).hexdigest()[:8]
        else:
            profile_hash = "default"

        return f"{RedisService.CACHE_PREFIX}:{content_hash}:{analysis_type}:{profile_hash}"

    async def get_cached_response(
        self,
        images: list[tuple[str, str, str]],
        analysis_type: str,
        user_profile: dict[str, Any] | None = None,
        dietary_preferences: list[str] | None = None,
        health_conditions: list[str] | None = None,
    ) -> AIAnalysisResponse | None:
        """Retrieve cached response if available.

        Args:
            images: List of (base64_data, content_type, filename) tuples.
            analysis_type: Type of analysis.
            user_profile: Optional user profile.
            dietary_preferences: Optional dietary preferences.
            health_conditions: Optional health conditions.

        Returns:
            Cached AIAnalysisResponse if found, None otherwise.
        """
        if not settings.redis_enabled or not self._connected:
            return None

        if not self._circuit_breaker.can_execute():
            logger.debug("Circuit breaker is open, skipping cache lookup")
            return None

        cache_key = self._generate_cache_key(
            images, analysis_type, user_profile, dietary_preferences, health_conditions
        )

        try:
            cached_data = await self._client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for key: {cache_key[:50]}...")
                self._circuit_breaker.record_success()

                # Deserialize using Pydantic
                response = AIAnalysisResponse.model_validate_json(cached_data)
                return response

            logger.debug(f"Cache MISS for key: {cache_key[:50]}...")
            self._circuit_breaker.record_success()
            return None

        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
            self._circuit_breaker.record_failure()
            return None

    async def cache_response(
        self,
        response: AIAnalysisResponse,
        images: list[tuple[str, str, str]],
        analysis_type: str,
        user_profile: dict[str, Any] | None = None,
        dietary_preferences: list[str] | None = None,
        health_conditions: list[str] | None = None,
        ttl: int | None = None,
    ) -> bool:
        """Cache an analysis response.

        Args:
            response: The AIAnalysisResponse to cache.
            images: List of (base64_data, content_type, filename) tuples.
            analysis_type: Type of analysis.
            user_profile: Optional user profile.
            dietary_preferences: Optional dietary preferences.
            health_conditions: Optional health conditions.
            ttl: Optional TTL override in seconds.

        Returns:
            True if caching successful, False otherwise.
        """
        if not settings.redis_enabled or not self._connected:
            return False

        if not self._circuit_breaker.can_execute():
            logger.debug("Circuit breaker is open, skipping cache write")
            return False

        cache_key = self._generate_cache_key(
            images, analysis_type, user_profile, dietary_preferences, health_conditions
        )

        ttl = ttl or settings.redis_cache_ttl

        try:
            # Serialize using Pydantic
            cached_data = response.model_dump_json()

            await self._client.setex(cache_key, ttl, cached_data)

            logger.info(f"Cached response with key: {cache_key[:50]}... (TTL: {ttl}s)")
            self._circuit_breaker.record_success()
            return True

        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
            self._circuit_breaker.record_failure()
            return False

    async def invalidate_cache(self, pattern: str = "*") -> int:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Glob pattern to match cache keys (default: all keys).

        Returns:
            Number of keys deleted.
        """
        if not settings.redis_enabled or not self._connected:
            return 0

        try:
            full_pattern = f"{self.CACHE_PREFIX}:{pattern}"
            keys = []
            async for key in self._client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                deleted = await self._client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching: {full_pattern}")
                return deleted
            return 0

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        if not settings.redis_enabled or not self._connected:
            return {"enabled": False}

        try:
            # Count cache keys
            key_count = 0
            async for _ in self._client.scan_iter(match=f"{self.CACHE_PREFIX}:*"):
                key_count += 1

            return {
                "enabled": True,
                "connected": self._connected,
                "circuit_state": self._circuit_breaker.state.value,
                "cached_entries": key_count,
                "ttl_seconds": settings.redis_cache_ttl,
            }

        except Exception as e:
            return {
                "enabled": True,
                "connected": False,
                "error": str(e),
            }


# Singleton instance for application-wide use
redis_service = RedisService()
