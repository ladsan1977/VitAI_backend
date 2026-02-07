"""Repository for AiConsumptionMetric model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ai_consumption_metric import AiConsumptionMetric
from .base import BaseRepository


class AiConsumptionMetricsRepository(BaseRepository[AiConsumptionMetric]):
    """
    Repository for AI consumption metrics operations.

    Provides methods for analytics queries including cache hit rates,
    cost calculations, token usage, and performance metrics.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with AiConsumptionMetric model."""
        super().__init__(AiConsumptionMetric, session)

    async def get_cache_hit_rate(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate cache hit rate for a time period.

        Args:
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Cache hit rate as percentage (0.0 to 1.0)
        """
        result = await self.session.execute(
            select(func.avg(cast(AiConsumptionMetric.cache_hit, Integer))).where(
                AiConsumptionMetric.created_at.between(start_date, end_date)
            )
        )
        return result.scalar() or 0.0

    async def get_total_openai_cost(self, start_date: datetime, end_date: datetime) -> Decimal:
        """
        Calculate total OpenAI costs for a time period.

        Args:
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Total cost in USD
        """
        result = await self.session.execute(
            select(func.sum(AiConsumptionMetric.openai_cost_usd)).where(
                AiConsumptionMetric.created_at.between(start_date, end_date)
            )
        )
        return result.scalar() or Decimal(0)

    async def get_average_response_time(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate average response time for a time period.

        Args:
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Average response time in milliseconds
        """
        result = await self.session.execute(
            select(func.avg(AiConsumptionMetric.response_time_ms)).where(
                AiConsumptionMetric.created_at.between(start_date, end_date)
            )
        )
        return result.scalar() or 0.0

    async def get_total_requests(self, start_date: datetime, end_date: datetime) -> int:
        """
        Count total AI analysis requests for a time period.

        Args:
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Total number of requests
        """
        result = await self.session.execute(
            select(func.count(AiConsumptionMetric.id)).where(
                AiConsumptionMetric.created_at.between(start_date, end_date)
            )
        )
        return result.scalar() or 0

    async def get_total_tokens(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Get total token usage for a time period.

        Args:
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Dictionary with total_tokens, prompt_tokens, completion_tokens
        """
        result = await self.session.execute(
            select(
                func.sum(AiConsumptionMetric.tokens_used).label("total_tokens"),
                func.sum(AiConsumptionMetric.prompt_tokens).label("prompt_tokens"),
                func.sum(AiConsumptionMetric.completion_tokens).label("completion_tokens"),
            ).where(AiConsumptionMetric.created_at.between(start_date, end_date))
        )
        row = result.one()
        return {
            "total_tokens": row.total_tokens or 0,
            "prompt_tokens": row.prompt_tokens or 0,
            "completion_tokens": row.completion_tokens or 0,
        }

    async def get_recent_metrics(self, limit: int = 100) -> list[AiConsumptionMetric]:
        """
        Get most recent metrics entries.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of AiConsumptionMetric instances ordered by creation date (newest first)
        """
        result = await self.session.execute(
            select(AiConsumptionMetric).order_by(AiConsumptionMetric.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
