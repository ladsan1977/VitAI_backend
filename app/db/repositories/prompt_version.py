"""Repository for PromptVersion model."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.prompt_version import PromptVersion
from .base import BaseRepository


class PromptVersionRepository(BaseRepository[PromptVersion]):
    """
    Repository for PromptVersion operations.

    Provides methods for managing prompt templates with versioning
    and activation control.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with PromptVersion model."""
        super().__init__(PromptVersion, session)

    async def get_active_prompt(self, language: str = "es") -> PromptVersion | None:
        """
        Get the active prompt for a specific language.

        Args:
            language: Language code (e.g., "es", "en")

        Returns:
            Active PromptVersion instance or None if not found
        """
        result = await self.session.execute(
            select(PromptVersion)
            .where(
                PromptVersion.language == language,
                PromptVersion.active == True,  # noqa: E712
            )
            .order_by(PromptVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_version(self, version: str, language: str = "es") -> PromptVersion | None:
        """
        Get a specific prompt version.

        Args:
            version: Version identifier (e.g., "v1.0", "v2.1")
            language: Language code (e.g., "es", "en")

        Returns:
            PromptVersion instance or None if not found
        """
        result = await self.session.execute(
            select(PromptVersion).where(PromptVersion.version == version, PromptVersion.language == language)
        )
        return result.scalar_one_or_none()

    async def get_all_versions(self, language: str | None = None) -> list[PromptVersion]:
        """
        Get all prompt versions, optionally filtered by language.

        Args:
            language: Optional language code to filter by

        Returns:
            List of PromptVersion instances ordered by creation date (newest first)
        """
        query = select(PromptVersion)

        if language:
            query = query.where(PromptVersion.language == language)

        query = query.order_by(PromptVersion.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def deactivate_all(self, language: str) -> None:
        """
        Deactivate all prompts for a specific language.

        Useful before activating a new version to ensure only one
        prompt is active per language at a time.

        Args:
            language: Language code (e.g., "es", "en")
        """
        result = await self.session.execute(
            select(PromptVersion).where(
                PromptVersion.language == language,
                PromptVersion.active == True,  # noqa: E712
            )
        )

        for prompt in result.scalars().all():
            prompt.active = False
            self.session.add(prompt)

        await self.session.flush()

    async def activate_version(self, version: str, language: str) -> PromptVersion | None:
        """
        Activate a specific prompt version.

        Deactivates all other prompts for the same language before
        activating the specified version.

        Args:
            version: Version identifier
            language: Language code

        Returns:
            Activated PromptVersion instance or None if not found
        """
        # First, deactivate all prompts for this language
        await self.deactivate_all(language)

        # Get the specific version
        prompt = await self.get_by_version(version, language)

        if prompt:
            prompt.active = True
            self.session.add(prompt)
            await self.session.flush()
            await self.session.refresh(prompt)

        return prompt
