"""Analysis controller for orchestrating product analysis workflow."""

import hashlib
import logging
import time
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.repositories.ai_consumption_metric import AiConsumptionMetricsRepository
from ..db.repositories.analysis import AnalysisRepository
from ..db.repositories.prompt_version import PromptVersionRepository
from ..models.ai import AIAnalysisResponse
from ..services.image_service import ImageService
from ..services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AnalysisController:
    """
    Controller for product analysis operations.

    Orchestrates the complete analysis workflow:
    1. Calculate image hash for deduplication
    2. Check database for existing analysis
    3. If not found, call OpenAI service
    4. Calculate costs
    5. Save results to database
    6. Return analysis response
    """

    _prompt_cache: str | None = None
    _prompt_cache_time: datetime | None = None
    _PROMPT_TTL_SECONDS: int = 300  # 5 minutes

    def __init__(
        self,
        openai_service: OpenAIService,
        image_service: ImageService,
    ):
        """
        Initialize controller with required services.

        Args:
            openai_service: Service for OpenAI API integration
            image_service: Service for image processing
        """
        self.openai_service = openai_service
        self.image_service = image_service

    async def analyze_product(
        self,
        request: Request,
        images: list[tuple[str, str, str]],  # (base64, mime_type, filename)
        analysis_type: str,
        user_profile: dict | None,
        dietary_preferences: list[str] | None,
        health_conditions: list[str] | None,
        db: AsyncSession,
        content_language: str = "es",
    ) -> AIAnalysisResponse:
        """
        Orchestrate product analysis workflow.

        This method implements the business logic for analyzing product images:
        - Checks for duplicate analyses using image hash
        - Returns cached results if available
        - Calls OpenAI service for new analyses
        - Persists results to database
        - Calculates and tracks OpenAI costs

        Args:
            request: FastAPI request object (for session_id)
            images: List of processed images (base64, mime_type, filename)
            analysis_type: Type of analysis to perform
            user_profile: Optional user profile data
            dietary_preferences: Optional dietary preferences
            health_conditions: Optional health conditions
            db: Async database session

        Returns:
            AIAnalysisResponse with analysis results

        Raises:
            Exception: If analysis fails or database operations fail
        """
        start_time = time.time()

        # Get session_id from request state (set by middleware)
        session_id = getattr(request.state, "session_id", None)

        # Create repositories
        analysis_repo = AnalysisRepository(db)
        consumption_repo = AiConsumptionMetricsRepository(db)

        # Calculate image hash for deduplication
        image_hash = self._calculate_image_hash(images)
        logger.info(f"Image hash calculated: {image_hash[:16]}...")

        # Check for existing analysis (deduplication)
        existing = await analysis_repo.get_by_image_hash(image_hash)
        if existing:
            logger.info(f"Found cached analysis for hash: {image_hash[:16]}...")
            cached_response = AIAnalysisResponse.model_validate(existing.analysis_result)
            # Update metadata for cached response
            cached_response.processing_time = 0.0

            # Record cache hit consumption metric
            response_time_ms = int((time.time() - start_time) * 1000)
            try:
                await consumption_repo.create(
                    {
                        "session_id": session_id,
                        "cache_hit": True,
                        "response_time_ms": response_time_ms,
                    }
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to save consumption metric: {e}")

            return cached_response

        # No cached analysis found, call OpenAI service
        logger.info("No cached analysis found, calling OpenAI service...")

        # Load prompt from database (with TTL cache)
        prompt_content = await self._get_prompt_content(db)

        analysis_result = await self.openai_service.analyze_nutrition_images(
            images=images,
            analysis_type=analysis_type,
            user_profile=user_profile,
            dietary_preferences=dietary_preferences,
            health_conditions=health_conditions,
            prompt_content=prompt_content,
            content_language=content_language,
        )

        # Calculate OpenAI cost
        openai_cost = self._calculate_openai_cost(analysis_result)

        # Save analysis to database
        try:
            await analysis_repo.create(
                {
                    "session_id": session_id,
                    "image_hash": image_hash,
                    "product_name": (analysis_result.product.name if analysis_result.product else None),
                    "analysis_result": analysis_result.model_dump(mode="json"),
                    "analysis_type": analysis_type,
                }
            )
            logger.info(f"Analysis saved to database with hash: {image_hash[:16]}...")
        except IntegrityError:
            # Race condition: another request saved the same analysis
            logger.warning("Duplicate analysis detected (race condition), fetching from DB")
            await db.rollback()
            existing = await analysis_repo.get_by_image_hash(image_hash)
            if existing:
                return AIAnalysisResponse.model_validate(existing.analysis_result)
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}")
            # Continue - don't fail the request if DB save fails

        # Save AI consumption metrics
        response_time_ms = int((time.time() - start_time) * 1000)
        try:
            await consumption_repo.create(
                {
                    "session_id": session_id,
                    "cache_hit": False,
                    "response_time_ms": response_time_ms,
                    "openai_cost_usd": openai_cost,
                    "tokens_used": analysis_result.tokens_used,
                    "prompt_tokens": analysis_result.prompt_tokens,
                    "completion_tokens": analysis_result.completion_tokens,
                }
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to save consumption metric: {e}")

        return analysis_result

    async def get_analysis_history(
        self,
        session_id: str,
        db: AsyncSession,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get analysis history for a session.

        Args:
            session_id: Session identifier
            db: Async database session
            limit: Maximum number of results to return

        Returns:
            List of analysis summaries with id, product_name, type, and timestamp
        """
        analysis_repo = AnalysisRepository(db)
        analyses = await analysis_repo.get_by_session_id(session_id, limit)

        return [
            {
                "id": str(analysis.id),
                "product_name": analysis.product_name,
                "analysis_type": analysis.analysis_type,
                "created_at": analysis.created_at.isoformat(),
            }
            for analysis in analyses
        ]

    async def get_analysis_by_id(
        self,
        analysis_id: str,
        db: AsyncSession,
    ) -> dict | None:
        """
        Get full analysis details by ID.

        Args:
            analysis_id: Analysis UUID
            db: Async database session

        Returns:
            Full analysis data or None if not found
        """
        import uuid

        analysis_repo = AnalysisRepository(db)

        try:
            analysis = await analysis_repo.get(uuid.UUID(analysis_id))
            if not analysis:
                return None

            return {
                "id": str(analysis.id),
                "session_id": analysis.session_id,
                "product_name": analysis.product_name,
                "analysis_type": analysis.analysis_type,
                "analysis_result": analysis.analysis_result,
                "created_at": analysis.created_at.isoformat(),
                "updated_at": analysis.updated_at.isoformat(),
            }
        except ValueError:
            # Invalid UUID format
            return None

    async def _get_prompt_content(self, db: AsyncSession) -> str | None:
        """
        Get the active prompt content from DB with a 5-minute TTL cache.

        Returns cached content if still fresh, otherwise queries the database.
        Falls back to None if no active prompt is found (service will use file).

        Args:
            db: Async database session

        Returns:
            Prompt content string or None if not found in DB
        """
        now = datetime.now(UTC)

        # Check if cached prompt is still valid
        if (
            AnalysisController._prompt_cache is not None
            and AnalysisController._prompt_cache_time is not None
            and (now - AnalysisController._prompt_cache_time).total_seconds() < self._PROMPT_TTL_SECONDS
        ):
            logger.debug("Using cached prompt from DB (TTL still valid)")
            return AnalysisController._prompt_cache

        # Cache is stale or missing, query DB
        try:
            prompt_repo = PromptVersionRepository(db)
            prompt = await prompt_repo.get_active_prompt(settings.prompt_language)

            if prompt:
                AnalysisController._prompt_cache = prompt.content
                AnalysisController._prompt_cache_time = now
                logger.info(f"Loaded active prompt from DB: version={prompt.version}, language={prompt.language}")
                return prompt.content

            logger.warning("No active prompt found in DB, falling back to file")
            return None
        except Exception as e:
            logger.error(f"Failed to load prompt from DB: {e}, falling back to file")
            return None

    def _calculate_image_hash(self, images: list[tuple[str, str, str]]) -> str:
        """
        Calculate SHA-256 hash of image content for deduplication.

        Args:
            images: List of images (base64, mime_type, filename)

        Returns:
            SHA-256 hash as hexadecimal string
        """
        # Concatenate all image base64 data
        image_data = "".join(img[0] for img in images)
        return hashlib.sha256(image_data.encode()).hexdigest()

    def _calculate_openai_cost(self, response: AIAnalysisResponse) -> Decimal:
        """
        Calculate OpenAI API cost based on token usage.

        Uses model-specific pricing for input and output tokens.

        Args:
            response: AI analysis response with token usage data

        Returns:
            Total cost in USD as Decimal
        """
        if not response.tokens_used:
            return Decimal(0)

        # Model pricing (per 1000 tokens)
        # TODO: Move to config or database for easier updates
        model_pricing = {
            "gpt-5.1-chat-latest": {
                "input": Decimal("0.00001"),  # $0.01 per 1K input tokens
                "output": Decimal("0.00003"),  # $0.03 per 1K output tokens
            },
            "gpt-4o": {
                "input": Decimal("0.0000025"),
                "output": Decimal("0.00001"),
            },
        }

        pricing = model_pricing.get(response.model_used, {})
        if not pricing:
            logger.warning(f"No pricing data for model: {response.model_used}")
            return Decimal(0)

        input_cost = Decimal(response.prompt_tokens or 0) * pricing.get("input", Decimal(0))
        output_cost = Decimal(response.completion_tokens or 0) * pricing.get("output", Decimal(0))

        return input_cost + output_cost
