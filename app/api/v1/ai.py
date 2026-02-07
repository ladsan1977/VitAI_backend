"""AI endpoints for nutritional analysis."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...controllers.analysis_controller import AnalysisController
from ...core.exceptions import (
    AnalysisValidationError,
    ImageProcessingError,
    NoImagesProvidedError,
    OpenAIServiceError,
    VitAIException,
)
from ...core.rate_limit import limiter
from ...core.security import verify_api_key
from ...db.session import get_db
from ...models.ai import AIAnalysisResponse
from ...services.image_service import ImageService
from ...services.openai_service import OpenAIService
from ...services.redis_service import redis_service
from ...utils.validators import validate_analysis_request_data, validate_multiple_images

router = APIRouter(prefix="/ai", tags=["AI Analysis"])

# Initialize services
openai_service = OpenAIService()
image_service = ImageService()

# Initialize controller
analysis_controller = AnalysisController(
    openai_service=openai_service,
    image_service=image_service,
)


@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_200_OK,
    summary="Analyze nutrition information from product images",
    description=f"""
    Analyze nutrition information from one or more product images using AI.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.

    This endpoint accepts:
    - Multiple images (nutrition facts, ingredients list, product packaging)
    - Analysis configuration (type, user profile, dietary preferences)
    - Health conditions for personalized recommendations

    Returns comprehensive nutritional analysis including:
    - Extracted nutrition facts
    - Ingredients analysis with allergens and additives
    - Health scoring and personalized recommendations

    **Rate Limits:**
    - {settings.rate_limit_per_minute} requests per minute
    - {settings.rate_limit_per_hour} requests per hour
    """,
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request data or images"},
        403: {"description": "Missing or invalid API key"},
        413: {"description": "File size too large"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error during analysis"},
    },
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute;{settings.rate_limit_per_hour}/hour")
async def analyze_nutrition(
    request: Request,
    images: Annotated[
        list[UploadFile],
        File(description="Product images (nutrition facts, ingredients, packaging). JPEG, PNG, or WebP format."),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
    analysis_type: Annotated[
        str | None, Form(description="Type of analysis: 'nutrition', 'ingredients', or 'complete'")
    ] = "complete",
    user_profile: Annotated[
        str | None, Form(description="User health profile as JSON string for personalized analysis")
    ] = None,
    dietary_preferences: Annotated[
        str | None, Form(description="Comma-separated dietary preferences (vegetarian, vegan, gluten-free, etc.)")
    ] = None,
    health_conditions: Annotated[
        str | None, Form(description="Comma-separated health conditions for personalized recommendations")
    ] = None,
    content_language: Annotated[
        str | None, Form(description="Language for AI-generated content: 'es' (Spanish) or 'en' (English)")
    ] = "es",
) -> AIAnalysisResponse:
    """Analyze nutrition information from product images."""

    try:
        # Validate that images are provided
        if not images or len(images) == 0:
            raise NoImagesProvidedError("At least one image must be provided for analysis")

        # Validate all uploaded images
        await validate_multiple_images(images)

        # Prepare request data
        request_data = {
            "analysis_type": analysis_type,
            "user_profile": user_profile,
            "dietary_preferences": dietary_preferences,
            "health_conditions": health_conditions,
        }

        # Validate and clean request data
        validated_data = validate_analysis_request_data(request_data)

        # Parse user_profile if provided
        user_profile_dict = None
        if validated_data.get("user_profile"):
            try:
                user_profile_dict = json.loads(validated_data["user_profile"])
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format in user_profile"
                ) from e

        # Process images
        processed_images = await image_service.process_multiple_files(images)

        # Call controller for business logic orchestration
        analysis_result = await analysis_controller.analyze_product(
            request=request,
            images=processed_images,
            analysis_type=validated_data.get("analysis_type", "complete"),
            user_profile=user_profile_dict,
            dietary_preferences=validated_data.get("dietary_preferences"),
            health_conditions=validated_data.get("health_conditions"),
            db=db,
            content_language=content_language or "es",
        )

        return analysis_result

    except NoImagesProvidedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    except (ImageProcessingError, AnalysisValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    except OpenAIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI analysis service temporarily unavailable"
        ) from e

    except VitAIException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during analysis"
        ) from e


@router.get("/health", summary="AI service health check", description="Check if the AI analysis service is operational")
async def ai_health_check():
    """Health check for AI service."""
    from ...config import settings

    return {
        "status": "ok",
        "service": "AI Analysis",
        "model": settings.openai_model,
        "api": "responses",
        "features": ["nutrition_extraction", "ingredient_analysis", "health_scoring"],
    }


@router.get(
    "/cache/stats",
    summary="Cache statistics",
    description="Get cache statistics and status (requires API key)",
    dependencies=[Depends(verify_api_key)],
)
async def cache_stats():
    """Get cache statistics and health status."""
    stats = await redis_service.get_cache_stats()
    health = await redis_service.health_check()

    return {
        "cache": stats,
        "health": health,
    }
