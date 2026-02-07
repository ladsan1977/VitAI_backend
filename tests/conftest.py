"""Test configuration and fixtures for VitAI backend tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import verify_api_key
from app.db.session import get_db
from app.main import app
from app.models.ai import (
    AIAnalysisResponse,
    GeneralRating,
    NutritionalEvaluation,
    ProductClassification,
    ProductInfo,
)


def override_verify_api_key():
    """Override API key verification for tests - always returns a valid key."""
    return "test_api_key"


async def override_get_db():
    """Override database dependency with a mock async session."""
    session = AsyncMock()
    yield session


@pytest.fixture
def client():
    """Create a test client with dependency overrides."""
    # Override the API key verification dependency
    app.dependency_overrides[verify_api_key] = override_verify_api_key
    # Override database session to avoid real DB connections
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_analysis_response():
    """Create a mock AIAnalysisResponse matching the current model structure."""
    return AIAnalysisResponse(
        analysis_id="test-analysis-123",
        product=ProductInfo(
            nombre="Test Product",
            marca="Test Brand",
            tamano_porcion="100g",
            porciones_por_envase="5",
        ),
        ingredientes=["ingredient1", "ingredient2", "ingredient3"],
        alergenos_identificados=["gluten", "soy"],
        clasificacion_producto=ProductClassification(
            nivel_procesamiento="NOVA 3",
            categoria_alimento="Snacks",
            categoria_riesgo="moderado",
        ),
        calificacion_general=GeneralRating(
            puntuacion=6.5,
            categoria_producto="Snacks",
            nivel_procesamiento="NOVA 3",
            categoria_riesgo="moderado",
            justificacion="Test justification for general score",
        ),
        evaluacion_nutricional=NutritionalEvaluation(
            fortalezas=["Good protein content"],
            debilidades=["High sodium"],
            advertencias=["Contains artificial sweeteners"],
        ),
        images_processed=1,
        processing_time=1.5,
        confidence_score=0.85,
        success=True,
    )


@pytest.fixture
def mock_controller(mock_analysis_response):
    """Mock the AnalysisController.analyze_product method."""
    with patch(
        "app.api.v1.ai.analysis_controller.analyze_product",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = mock_analysis_response
        yield mock
