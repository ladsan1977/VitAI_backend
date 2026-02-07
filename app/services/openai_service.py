"""OpenAI service for AI-powered nutritional analysis."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import settings
from ..core.exceptions import AnalysisValidationError, OpenAIServiceError
from ..models.ai import (
    AIAnalysisResponse,
    GeneralRating,
    IdentifiedAdditives,
    NutritionalEvaluation,
    PortionInfo,
    ProductClassification,
    ProductInfo,
    ProfileRating,
    Recommendations,
    ScoreBreakdown,
)
from .redis_service import redis_service

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API for nutritional analysis."""

    def __init__(self):
        """Initialize OpenAI service."""
        import openai

        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.prompt_cache: str | None = None  # Cache del contenido del prompt

    async def analyze_nutrition_images(
        self,
        images: list[tuple[str, str, str]],  # (base64_data, content_type, filename)
        analysis_type: str = "complete",
        user_profile: dict[str, Any] | None = None,
        dietary_preferences: list[str] | None = None,
        health_conditions: list[str] | None = None,
        prompt_content: str | None = None,
        content_language: str = "es",
    ) -> AIAnalysisResponse:
        """Analyze nutrition information from product images."""
        start_time = datetime.now(UTC)
        analysis_id = str(uuid.uuid4())

        try:
            # Check cache first
            cached_response = await redis_service.get_cached_response(
                images=images,
                analysis_type=analysis_type,
                user_profile=user_profile,
                dietary_preferences=dietary_preferences,
                health_conditions=health_conditions,
            )

            if cached_response:
                # Update metadata for cached response
                cached_response.analysis_id = analysis_id
                cached_response.processing_time = (datetime.now(UTC) - start_time).total_seconds()
                logger.info(f"Returning cached response for analysis_id: {analysis_id}")
                return cached_response

            # Build prompt
            prompt = self._build_analysis_prompt(
                analysis_type, user_profile, dietary_preferences, health_conditions, prompt_content, content_language
            )

            # Prepare images
            image_messages = self._prepare_image_messages(images)

            # Make real API call
            response_data, token_usage = await self._real_openai_call(prompt, image_messages, analysis_type)

            # Parse and validate
            analysis_response = self._parse_openai_response(
                response_data, analysis_id, len(images), start_time, token_usage
            )

            # Cache the response asynchronously (fire and forget)
            asyncio.create_task(
                redis_service.cache_response(
                    response=analysis_response,
                    images=images,
                    analysis_type=analysis_type,
                    user_profile=user_profile,
                    dietary_preferences=dietary_preferences,
                    health_conditions=health_conditions,
                )
            )

            return analysis_response

        except Exception as e:
            raise OpenAIServiceError(
                f"Failed to analyze images: {str(e)}",
                details={
                    "analysis_id": analysis_id,
                    "images_count": len(images),
                    "error": str(e),
                },
            ) from e

    # -------------------------------------------------------------------------
    # 🧩 NUEVO MÉTODO: carga dinámica del prompt con cache
    # -------------------------------------------------------------------------
    def _build_analysis_prompt(
        self,
        analysis_type: str,
        user_profile: dict[str, Any] | None = None,
        dietary_preferences: list[str] | None = None,
        health_conditions: list[str] | None = None,
        prompt_content: str | None = None,
        content_language: str = "es",
    ) -> str:
        """Build the analysis prompt for OpenAI using DB content or fallback file."""
        try:
            if prompt_content is not None:
                # Use prompt from database
                base_prompt = prompt_content
                logger.debug("Using prompt loaded from database")
            else:
                # Fallback: load from local markdown file (legacy Spanish prompt)
                logger.warning("No DB prompt provided, falling back to local file (may contain Spanish JSON keys)")
                prompt_path = Path(__file__).parent / "prompts" / "prompt_produccion_nutricional_v2.md"

                if self.prompt_cache is None:
                    if not prompt_path.exists():
                        raise FileNotFoundError(f"Prompt file not found at: {prompt_path}")
                    self.prompt_cache = prompt_path.read_text(encoding="utf-8")

                base_prompt = self.prompt_cache

            # Analysis focus
            if analysis_type == "nutrition":
                focus_section = "Analysis focus: Prioritize extraction of nutritional data and per-serving values."
            elif analysis_type == "ingredients":
                focus_section = "Analysis focus: Prioritize ingredient list, allergens, and additives."
            else:
                focus_section = "Analysis focus: Provide a complete analysis: nutrition, ingredients, and comprehensive health evaluation."

            # Personalization
            personalization = ""
            if dietary_preferences or health_conditions or user_profile:
                personalization += "\n\n## Personalization\n"
                if dietary_preferences:
                    personalization += f"- Dietary preferences: {', '.join(dietary_preferences)}\n"
                if health_conditions:
                    personalization += f"- Health conditions to consider: {', '.join(health_conditions)}\n"
                if user_profile:
                    personalization += f"- User profile: {json.dumps(user_profile, ensure_ascii=False)}\n"

            # Content language instruction
            lang_names = {"es": "Spanish", "en": "English"}
            lang_name = lang_names.get(content_language, content_language)
            language_instruction = (
                f"\n\nIMPORTANT: Write ALL text content (justifications, summaries, "
                f"recommendations, warnings, strengths, weaknesses) in {lang_name}."
            )

            # Assemble final prompt
            full_prompt = f"{base_prompt}\n\n{focus_section}\n{personalization}{language_instruction}"

            return full_prompt.strip()

        except Exception as e:
            raise OpenAIServiceError(f"Error building analysis prompt: {str(e)}") from e

    # -------------------------------------------------------------------------
    # Conversión numérica
    # -------------------------------------------------------------------------
    def _convert_to_float(self, value: Any) -> float | None:
        """Convert string or numeric value to float, handling various formats."""
        if value is None:
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                cleaned = value.strip().lower()
                for unit in ["g", "mg", "kcal", "kj"]:
                    cleaned = cleaned.replace(unit, "")
                cleaned = cleaned.strip()
                return float(cleaned) if cleaned else None
            except (ValueError, AttributeError):
                return None
        return None

    # -------------------------------------------------------------------------
    # Preparación de imágenes
    # -------------------------------------------------------------------------
    def _prepare_image_messages(self, images: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
        """Prepare image messages for OpenAI Responses API."""
        return [
            {
                "type": "input_image",
                "image_url": f"data:{content_type};base64,{base64_data}",
            }
            for base64_data, content_type, _ in images
        ]

    # -------------------------------------------------------------------------
    # Mock para desarrollo
    # -------------------------------------------------------------------------
    async def _mock_openai_call(
        self, prompt: str, image_messages: list[dict[str, Any]], analysis_type: str
    ) -> dict[str, Any]:
        """Mock OpenAI API call for development."""
        return {
            "nutritional_info": {"product_name": "Sample Product", "calories": 150.0},
            "health_analysis": {"overall_score": 6.5, "sugar_level": "medium"},
            "confidence_score": 0.85,
        }

    # -------------------------------------------------------------------------
    # Llamada real a OpenAI
    # -------------------------------------------------------------------------
    async def _real_openai_call(
        self, prompt: str, image_messages: list[dict[str, Any]], analysis_type: str
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """Make real OpenAI API call using Responses API for nutritional analysis.

        Returns:
            Tuple of (response_data, token_usage) where token_usage contains:
            - total_tokens: Total tokens used
            - prompt_tokens: Tokens in the prompt
            - completion_tokens: Tokens in the completion
        """
        try:
            input_messages = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an expert nutritional analyst. "
                                "You must follow exactly the steps and rules in the prompt. "
                                "Do not ignore any scoring coherence conditions. "
                                "If the general_rating score is less than 5, no individual profile score can be greater than 7. "
                                "Return ONLY valid JSON, with no additional text or explanation outside the JSON."
                            ),
                        }
                    ],
                },
                {"role": "user", "content": [{"type": "input_text", "text": prompt}] + image_messages},
            ]

            logger.info(f"Calling OpenAI API with model: {settings.openai_model}")
            response = await self.client.responses.create(
                model=settings.openai_model,
                input=input_messages,
                max_output_tokens=settings.openai_max_output_tokens,
                text={"format": {"type": "json_object"}},
            )

            content = response.output_text
            logger.debug(f"Raw OpenAI response length: {len(content) if content else 0} characters")
            if not content:
                raise ValueError("Empty response from OpenAI")

            if content.strip().startswith("```json"):
                logger.debug("Removing markdown code block wrapper from response")
                content = content.strip()[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            # Extract token usage (Responses API uses input_tokens/output_tokens)
            token_usage = {}
            if response.usage:
                token_usage = {
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.input_tokens,  # Responses API uses input_tokens
                    "completion_tokens": response.usage.output_tokens,  # Responses API uses output_tokens
                }
                logger.info(f"Token usage: {token_usage}")

            logger.debug("Parsing JSON response...")
            parsed_json = json.loads(content)
            logger.debug(f"JSON parsed successfully with keys: {list(parsed_json.keys())}")
            return parsed_json, token_usage

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI: {str(e)}")
            logger.error(f"JSON error at line {e.lineno}, column {e.colno}, position {e.pos}")

            # Show context around the error
            if content and e.pos:
                start = max(0, e.pos - 200)
                end = min(len(content), e.pos + 200)
                error_context = content[start:end]
                logger.error(f"Context around error: ...{error_context}...")

            # Log full content length and samples
            logger.error(f"Total content length: {len(content) if content else 0} characters")
            logger.error(f"Content sample (first 2000 chars): {content[:2000] if content else 'None'}")
            logger.error(f"Content sample (last 1000 chars): {content[-1000:] if content else 'None'}")

            raise OpenAIServiceError(f"Invalid JSON response from OpenAI: {str(e)}") from e
        except Exception as e:
            raise OpenAIServiceError(f"OpenAI API call failed: {str(e)}") from e

    # -------------------------------------------------------------------------
    # Response parsing
    # -------------------------------------------------------------------------
    def _parse_openai_response(
        self,
        response_data: dict[str, Any],
        analysis_id: str,
        images_count: int,
        start_time: datetime,
        token_usage: dict[str, int] | None = None,
    ) -> AIAnalysisResponse:
        """Parse OpenAI response into AIAnalysisResponse model."""
        try:
            logger.info(f"Starting to parse OpenAI response for analysis_id: {analysis_id}")
            logger.debug(f"Response data keys: {list(response_data.keys())}")

            processing_time = (datetime.now(UTC) - start_time).total_seconds()

            # ---------- Product ----------
            logger.debug("Parsing product...")
            product = (
                ProductInfo(
                    name=response_data.get("product", {}).get("name"),
                    brand=response_data.get("product", {}).get("brand"),
                    serving_size=response_data.get("product", {}).get("serving_size"),
                    servings_per_container=response_data.get("product", {}).get("servings_per_container"),
                )
                if "product" in response_data
                else None
            )
            logger.debug(f"Product parsed: {product is not None}")

            # ---------- Ingredients ----------
            logger.debug("Parsing ingredients...")
            ingredients = response_data.get("ingredients", [])
            logger.debug(f"Ingredients count: {len(ingredients)}")

            # ---------- Identified allergens ----------
            identified_allergens = response_data.get("identified_allergens", [])

            # ---------- Identified additives ----------
            identified_additives = None
            if "identified_additives" in response_data:
                adit_data = response_data["identified_additives"]
                identified_additives = IdentifiedAdditives(
                    sweeteners=adit_data.get("sweeteners", []),
                    colorants=adit_data.get("colorants", []),
                    preservatives=adit_data.get("preservatives", []),
                    flavorings=adit_data.get("flavorings", []),
                )

            # ---------- Nutritional information ----------
            nutritional_information = None
            if "nutritional_information" in response_data:
                serving_data = response_data["nutritional_information"].get("per_serving", {})
                nutritional_information = {"per_serving": PortionInfo(**serving_data)}

            # ---------- Product classification ----------
            product_classification = None
            if "product_classification" in response_data:
                clasif_data = response_data["product_classification"]
                product_classification = ProductClassification(
                    processing_level=clasif_data.get("processing_level", ""),
                    food_category=clasif_data.get("food_category"),
                    risk_category=clasif_data.get("risk_category", ""),
                )

            # ---------- Nutritional evaluation ----------
            nutritional_evaluation = None
            if "nutritional_evaluation" in response_data:
                eval_data = response_data["nutritional_evaluation"]
                nutritional_evaluation = NutritionalEvaluation(
                    strengths=eval_data.get("strengths", []),
                    weaknesses=eval_data.get("weaknesses", []),
                    warnings=eval_data.get("warnings", []),
                    reference_comparison=eval_data.get("reference_comparison"),
                )

            # ---------- Profile ratings ----------
            logger.debug("Parsing profile_ratings...")
            profile_ratings = {}
            if "profile_ratings" in response_data:
                logger.debug(f"Found profile_ratings with profiles: {list(response_data['profile_ratings'].keys())}")
                for profile, data in response_data["profile_ratings"].items():
                    try:
                        logger.debug(f"Parsing profile: {profile}")
                        profile_ratings[profile] = ProfileRating(
                            score=data.get("score"),
                            recommended_frequency=data.get("recommended_frequency"),
                            suggested_serving_size=data.get("suggested_serving_size"),
                            justification=data.get("justification", ""),
                        )
                        logger.debug(f"Successfully parsed profile: {profile}")
                    except Exception as e:
                        logger.error(f"Error parsing profile {profile}: {str(e)}", exc_info=True)
                        continue
            logger.debug(f"Total profile_ratings parsed: {len(profile_ratings)}")

            # ---------- General rating ----------
            logger.debug("Parsing general_rating...")
            general_rating = None
            if "general_rating" in response_data:
                gr_data = response_data["general_rating"]
                logger.debug(f"general_rating keys: {list(gr_data.keys())}")

                # Parse score_breakdown if present
                score_breakdown = None
                if "score_breakdown" in gr_data:
                    logger.debug("Parsing score_breakdown...")
                    sb_data = gr_data["score_breakdown"]
                    score_breakdown = ScoreBreakdown(**sb_data)
                    logger.debug("score_breakdown parsed successfully")

                general_rating = GeneralRating(
                    score=gr_data.get("score"),
                    score_breakdown=score_breakdown,
                    product_category=gr_data.get("product_category"),
                    processing_level=gr_data.get("processing_level"),
                    risk_category=gr_data.get("risk_category"),
                    justification=gr_data.get("justification", ""),
                )
                logger.debug("general_rating parsed successfully")

            # ---------- Recommendations ----------
            recommendations = None
            if "recommendations" in response_data:
                rec_data = response_data["recommendations"]
                recommendations = Recommendations(
                    general_consumption=rec_data.get("general_consumption"),
                    optimal_frequency=rec_data.get("optimal_frequency"),
                    suggested_alternatives=rec_data.get("suggested_alternatives", []),
                )

            # ---------- Executive summary ----------
            executive_summary = response_data.get("executive_summary")

            # ---------- Confidence score ----------
            confidence_score = float(response_data.get("confidence_score", 0.5))

            # ---------- Build response ----------
            logger.debug("Constructing AIAnalysisResponse...")
            response = AIAnalysisResponse(
                analysis_id=analysis_id,
                product=product,
                ingredients=ingredients,
                identified_allergens=identified_allergens,
                identified_additives=identified_additives,
                nutritional_information=nutritional_information,
                product_classification=product_classification,
                general_rating=general_rating,
                profile_ratings=profile_ratings,
                nutritional_evaluation=nutritional_evaluation,
                recommendations=recommendations,
                executive_summary=executive_summary,
                images_processed=images_count,
                processing_time=processing_time,
                confidence_score=confidence_score,
                model_used=settings.openai_model,
                tokens_used=token_usage.get("total_tokens") if token_usage else None,
                prompt_tokens=token_usage.get("prompt_tokens") if token_usage else None,
                completion_tokens=token_usage.get("completion_tokens") if token_usage else None,
            )
            logger.info(f"Successfully parsed OpenAI response for analysis_id: {analysis_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}", exc_info=True)
            logger.error(f"Response data structure: {json.dumps(response_data, indent=2, default=str)}")
            raise AnalysisValidationError(
                f"Failed to parse OpenAI response: {str(e)}",
                details={
                    "analysis_id": analysis_id,
                    "response_data": response_data,
                    "error": str(e),
                },
            ) from e
