"""Prompt controller for managing prompt versions."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.repositories.prompt_version import PromptVersionRepository

logger = logging.getLogger(__name__)


class PromptController:
    """
    Controller for prompt version management.

    Orchestrates prompt template operations including versioning,
    activation, and retrieval for multi-language support.
    """

    async def get_active_prompt(
        self,
        db: AsyncSession,
        language: str = "es",
    ) -> dict | None:
        """
        Get the currently active prompt for a language.

        Args:
            db: Async database session
            language: Language code (default: "es")

        Returns:
            Prompt data dictionary or None if not found
        """
        prompt_repo = PromptVersionRepository(db)
        prompt = await prompt_repo.get_active_prompt(language)

        if not prompt:
            logger.warning(f"No active prompt found for language: {language}")
            return None

        return {
            "id": str(prompt.id),
            "version": prompt.version,
            "language": prompt.language,
            "content": prompt.content,
            "active": prompt.active,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
        }

    async def create_prompt_version(
        self,
        db: AsyncSession,
        version: str,
        language: str,
        content: str,
        activate: bool = False,
    ) -> dict:
        """
        Create a new prompt version.

        Optionally activates the new version, deactivating all others
        for the same language.

        Args:
            db: Async database session
            version: Version identifier (e.g., "v1.0", "v2.1")
            language: Language code (e.g., "es", "en")
            content: Prompt template content
            activate: Whether to activate this version immediately

        Returns:
            Created prompt data dictionary
        """
        prompt_repo = PromptVersionRepository(db)

        # Create the new prompt version
        prompt = await prompt_repo.create(
            {
                "version": version,
                "language": language,
                "content": content,
                "active": False,  # Start inactive, activate separately if needed
            }
        )

        # Activate if requested
        if activate:
            await prompt_repo.activate_version(version, language)
            await db.refresh(prompt)

        logger.info(f"Created prompt version {version} for language {language} " f"(active={prompt.active})")

        return {
            "id": str(prompt.id),
            "version": prompt.version,
            "language": prompt.language,
            "content": prompt.content,
            "active": prompt.active,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
        }

    async def activate_prompt_version(
        self,
        db: AsyncSession,
        version: str,
        language: str,
    ) -> dict | None:
        """
        Activate a specific prompt version.

        Automatically deactivates all other prompts for the same language.

        Args:
            db: Async database session
            version: Version identifier to activate
            language: Language code

        Returns:
            Activated prompt data or None if version not found
        """
        prompt_repo = PromptVersionRepository(db)

        prompt = await prompt_repo.activate_version(version, language)

        if not prompt:
            logger.warning(f"Failed to activate prompt version {version} for language {language}")
            return None

        logger.info(f"Activated prompt version {version} for language {language}")

        return {
            "id": str(prompt.id),
            "version": prompt.version,
            "language": prompt.language,
            "content": prompt.content,
            "active": prompt.active,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
        }

    async def list_prompt_versions(
        self,
        db: AsyncSession,
        language: str | None = None,
    ) -> list[dict]:
        """
        List all prompt versions, optionally filtered by language.

        Args:
            db: Async database session
            language: Optional language code to filter by

        Returns:
            List of prompt version summaries
        """
        prompt_repo = PromptVersionRepository(db)
        prompts = await prompt_repo.get_all_versions(language)

        return [
            {
                "id": str(prompt.id),
                "version": prompt.version,
                "language": prompt.language,
                "active": prompt.active,
                "created_at": prompt.created_at.isoformat(),
                "content_preview": (prompt.content[:100] + "..." if len(prompt.content) > 100 else prompt.content),
            }
            for prompt in prompts
        ]

    async def get_prompt_by_version(
        self,
        db: AsyncSession,
        version: str,
        language: str,
    ) -> dict | None:
        """
        Get full details of a specific prompt version.

        Args:
            db: Async database session
            version: Version identifier
            language: Language code

        Returns:
            Full prompt data or None if not found
        """
        prompt_repo = PromptVersionRepository(db)
        prompt = await prompt_repo.get_by_version(version, language)

        if not prompt:
            logger.warning(f"Prompt version {version} not found for language {language}")
            return None

        return {
            "id": str(prompt.id),
            "version": prompt.version,
            "language": prompt.language,
            "content": prompt.content,
            "active": prompt.active,
            "created_at": prompt.created_at.isoformat(),
            "updated_at": prompt.updated_at.isoformat(),
        }
