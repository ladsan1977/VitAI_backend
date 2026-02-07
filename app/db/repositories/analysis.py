"""Repository for Analysis model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analysis import Analysis
from .base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    """
    Repository for Analysis operations.

    Provides methods for querying product analyses with deduplication
    via image hash and session-based history retrieval.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with Analysis model."""
        super().__init__(Analysis, session)

    async def get_by_image_hash(self, image_hash: str) -> Analysis | None:
        """
        Get analysis by image hash for deduplication.

        Args:
            image_hash: SHA-256 hash of image content

        Returns:
            Analysis instance or None if not found
        """
        result = await self.session.execute(select(Analysis).where(Analysis.image_hash == image_hash))
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: str, limit: int = 10) -> list[Analysis]:
        """
        Get analysis history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of results to return

        Returns:
            List of Analysis instances ordered by creation date (newest first)
        """
        result = await self.session.execute(
            select(Analysis).where(Analysis.session_id == session_id).order_by(Analysis.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_analyses(self, limit: int = 50) -> list[Analysis]:
        """
        Get most recent analyses across all sessions.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of Analysis instances ordered by creation date (newest first)
        """
        result = await self.session.execute(select(Analysis).order_by(Analysis.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def count_by_session_id(self, session_id: str) -> int:
        """
        Count total analyses for a session.

        Args:
            session_id: Session identifier

        Returns:
            Total count of analyses for the session
        """
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(Analysis.id)).where(Analysis.session_id == session_id))
        return result.scalar() or 0
