"""Analytics controller for AI consumption metrics and reporting."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.repositories.ai_consumption_metric import AiConsumptionMetricsRepository

logger = logging.getLogger(__name__)


class AnalyticsController:
    """
    Controller for analytics operations.

    Orchestrates metrics queries and provides business logic for
    AI consumption reporting, cost analysis, and performance metrics.
    """

    async def get_metrics_summary(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Get comprehensive AI consumption metrics summary for a time period.

        Args:
            db: Async database session
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with metrics summary including token usage
        """
        metrics_repo = AiConsumptionMetricsRepository(db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        cache_hit_rate = await metrics_repo.get_cache_hit_rate(start_date, end_date)
        total_cost = await metrics_repo.get_total_openai_cost(start_date, end_date)
        avg_response_time = await metrics_repo.get_average_response_time(start_date, end_date)
        total_requests = await metrics_repo.get_total_requests(start_date, end_date)
        token_usage = await metrics_repo.get_total_tokens(start_date, end_date)

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cache_hit_rate": round(float(cache_hit_rate), 4),
            "cache_hit_percentage": round(float(cache_hit_rate) * 100, 2),
            "total_requests": total_requests,
            "total_openai_cost_usd": float(total_cost),
            "average_response_time_ms": round(float(avg_response_time), 2),
            "token_usage": token_usage,
        }

    async def get_cost_breakdown(
        self,
        db: AsyncSession,
        days: int = 30,
    ) -> dict:
        """
        Get detailed cost breakdown analysis.

        Args:
            db: Async database session
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with cost breakdown
        """
        metrics_repo = AiConsumptionMetricsRepository(db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        total_cost = await metrics_repo.get_total_openai_cost(start_date, end_date)
        total_requests = await metrics_repo.get_total_requests(start_date, end_date)
        token_usage = await metrics_repo.get_total_tokens(start_date, end_date)

        cost_per_request = float(total_cost) / total_requests if total_requests > 0 else 0
        daily_average_cost = float(total_cost) / days if days > 0 else 0

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_cost_usd": float(total_cost),
            "total_requests": total_requests,
            "cost_per_request_usd": round(cost_per_request, 6),
            "daily_average_cost_usd": round(daily_average_cost, 4),
            "projected_monthly_cost_usd": round(daily_average_cost * 30, 2),
            "token_usage": token_usage,
        }

    async def get_performance_metrics(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Get performance-focused metrics.

        Args:
            db: Async database session
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with performance metrics
        """
        metrics_repo = AiConsumptionMetricsRepository(db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        avg_response_time = await metrics_repo.get_average_response_time(start_date, end_date)
        cache_hit_rate = await metrics_repo.get_cache_hit_rate(start_date, end_date)
        total_requests = await metrics_repo.get_total_requests(start_date, end_date)

        # Calculate cache savings (approximate)
        # Assume cache hit saves ~1000ms on average
        estimated_time_saved_ms = int(cache_hit_rate * total_requests) * 1000

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "average_response_time_ms": round(float(avg_response_time), 2),
            "cache_hit_rate": round(float(cache_hit_rate), 4),
            "cache_hit_percentage": round(float(cache_hit_rate) * 100, 2),
            "total_requests": total_requests,
            "estimated_time_saved_ms": estimated_time_saved_ms,
            "estimated_time_saved_hours": round(estimated_time_saved_ms / 3600000, 2),
        }
