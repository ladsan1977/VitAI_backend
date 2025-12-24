"""AI endpoints for nutritional analysis."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from ...config import settings
from ...core.exceptions import (
    AnalysisValidationError,
    ImageProcessingError,
    NoImagesProvidedError,
    OpenAIServiceError,
    VitAIException,
)
from ...core.rate_limit import limiter
from ...core.security import verify_api_key
from ...models.ai import AIAnalysisResponse
from ...services.image_service import ImageService
from ...services.openai_service import OpenAIService
from ...utils.validators import validate_analysis_request_data, validate_multiple_images

router = APIRouter(prefix="/ai", tags=["AI Analysis"])

# Initialize services
openai_service = OpenAIService()
image_service = ImageService()


@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
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

        # Perform AI analysis
        analysis_result = await openai_service.analyze_nutrition_images(
            images=processed_images,
            analysis_type=validated_data.get("analysis_type", "complete"),
            user_profile=user_profile_dict,
            dietary_preferences=validated_data.get("dietary_preferences"),
            health_conditions=validated_data.get("health_conditions"),
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
