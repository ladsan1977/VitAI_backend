"""Analytics endpoints for metrics and reporting."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...controllers.analysis_controller import AnalysisController
from ...controllers.analytics_controller import AnalyticsController
from ...core.security import verify_api_key
from ...db.session import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Initialize controllers
analytics_controller = AnalyticsController()
analysis_controller = AnalysisController(None, None)  # Only uses DB, no services needed


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get metrics summary",
    description="""
    Get comprehensive AI consumption metrics for the specified time period.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.

    Returns aggregated metrics including:
    - Cache hit rate and percentage
    - Total AI analysis requests
    - Average response time
    - Total OpenAI API costs
    - Token usage breakdown
    """,
    dependencies=[Depends(verify_api_key)],
)
async def get_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze (1-90)"),
):
    """
    Get metrics summary including cache performance, costs, and response times.

    Args:
        days: Number of days to analyze (default: 7)
        db: Database session

    Returns:
        Dictionary with metrics summary
    """
    return await analytics_controller.get_metrics_summary(db=db, days=days)


@router.get(
    "/costs",
    status_code=status.HTTP_200_OK,
    summary="Get cost breakdown",
    description="""
    Get detailed OpenAI API cost analysis.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.

    Returns cost analytics including:
    - Total costs for the period
    - Cost per request
    - Daily average costs
    - Projected monthly costs
    """,
    dependencies=[Depends(verify_api_key)],
)
async def get_cost_breakdown(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze (1-365)"),
):
    """
    Get cost breakdown with projections.

    Args:
        days: Number of days to analyze (default: 30)
        db: Database session

    Returns:
        Dictionary with cost analysis
    """
    return await analytics_controller.get_cost_breakdown(db=db, days=days)


@router.get(
    "/performance",
    status_code=status.HTTP_200_OK,
    summary="Get performance metrics",
    description="""
    Get performance-focused metrics including response times and cache efficiency.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.

    Returns performance analytics including:
    - Average response time
    - Cache hit rate and percentage
    - Estimated time saved by caching
    """,
    dependencies=[Depends(verify_api_key)],
)
async def get_performance_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze (1-90)"),
):
    """
    Get performance metrics with cache analysis.

    Args:
        days: Number of days to analyze (default: 7)
        db: Database session

    Returns:
        Dictionary with performance metrics
    """
    return await analytics_controller.get_performance_metrics(db=db, days=days)


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Get analysis history",
    description="""
    Get analysis history for the current session.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.

    Returns a list of recent analyses for the current session.
    """,
    dependencies=[Depends(verify_api_key)],
)
async def get_analysis_history(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results to return (1-50)"),
):
    """
    Get analysis history for the current session.

    Args:
        request: FastAPI request (for session_id)
        limit: Maximum number of results (default: 10)
        db: Database session

    Returns:
        Dictionary with history list
    """
    session_id = getattr(request.state, "session_id", None)

    if not session_id:
        return {"history": []}

    history = await analysis_controller.get_analysis_history(
        session_id=session_id,
        db=db,
        limit=limit,
    )

    return {"history": history}


@router.get(
    "/history/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Get analysis details",
    description="""
    Get full details of a specific analysis by ID.

    **Authentication Required:** This endpoint requires an API key in the `X-API-Key` header.
    """,
    dependencies=[Depends(verify_api_key)],
)
async def get_analysis_details(
    analysis_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get full analysis details by ID.

    Args:
        analysis_id: Analysis UUID
        db: Database session

    Returns:
        Analysis details or 404 if not found
    """
    from fastapi import HTTPException

    analysis = await analysis_controller.get_analysis_by_id(
        analysis_id=analysis_id,
        db=db,
    )

    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return analysis
