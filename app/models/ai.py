"""AI-related Pydantic models for request/response validation."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse


class NutritionalInfo(BaseModel):
    """Nutritional information extracted from product images."""

    # Basic product info
    product_name: str | None = None
    brand: str | None = None
    serving_size: str | None = None
    servings_per_container: str | None = None

    # Nutritional values per serving
    calories: float | None = None
    total_fat: float | None = None
    saturated_fat: float | None = None
    trans_fat: float | None = None
    cholesterol: float | None = None
    sodium: float | None = None
    total_carbohydrates: float | None = None
    dietary_fiber: float | None = None
    total_sugars: float | None = None
    added_sugars: float | None = None
    protein: float | None = None

    # Vitamins and minerals
    vitamin_d: float | None = None
    calcium: float | None = None
    iron: float | None = None
    potassium: float | None = None

    # Additional nutrients (if present)
    additional_nutrients: dict[str, float] | None = None


class Ingredient(BaseModel):
    """Individual ingredient information."""

    name: str
    position: int = Field(..., description="Position in ingredient list (1-based)")
    category: str | None = None
    allergen: bool = False
    additives: list[str] = Field(default_factory=list)


class IngredientsInfo(BaseModel):
    """Ingredients information extracted from product images."""

    ingredients: list[Ingredient]
    allergens: list[str] = Field(default_factory=list)
    may_contain: list[str] = Field(default_factory=list)
    additives_summary: list[str] = Field(default_factory=list)


class HealthAnalysis(BaseModel):
    """Health analysis based on nutritional and ingredient information."""

    overall_score: float = Field(..., ge=0, le=10, description="Overall health score (0-10)")
    nutritional_score: float = Field(..., ge=0, le=10)
    ingredients_score: float = Field(..., ge=0, le=10)

    # Analysis categories
    caloric_density: str | None = Field(default=None, description="low/medium/high")
    sodium_level: str | None = Field(default=None, description="low/medium/high")
    sugar_level: str | None = Field(default=None, description="low/medium/high")
    processing_level: str | None = Field(default=None, description="minimal/moderate/ultra-processed")

    # Health insights
    positive_aspects: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AIAnalysisRequest(BaseModel):
    """Request model for AI analysis endpoint."""

    analysis_type: str = Field(
        default="complete", description="Type of analysis: 'nutrition', 'ingredients', 'complete'"
    )
    user_profile: dict[str, Any] | None = Field(
        default=None, description="User health profile for personalized analysis"
    )
    dietary_preferences: list[str] | None = Field(
        default=None, description="User dietary preferences (vegetarian, vegan, gluten-free, etc.)"
    )
    health_conditions: list[str] | None = Field(
        default=None, description="User health conditions for personalized recommendations"
    )


class ProductInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, alias="nombre")
    brand: str | None = Field(default=None, alias="marca")
    serving_size: str | None = Field(default=None, alias="tamano_porcion")
    servings_per_container: str | None = Field(default=None, alias="porciones_por_envase")


class PortionInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    calories: float | None = Field(default=None, alias="calorias")
    total_fat: float | None = Field(default=None, alias="grasas_totales")
    saturated_fat: float | None = Field(default=None, alias="grasas_saturadas")
    trans_fat: float | None = Field(default=None, alias="grasas_trans")
    total_carbohydrates: float | None = Field(default=None, alias="carbohidratos_totales")
    fiber: float | None = Field(default=None, alias="fibra")
    total_sugars: float | None = Field(default=None, alias="azucares_totales")
    added_sugars: float | None = Field(default=None, alias="azucares_anadidos")
    protein: float | None = Field(default=None, alias="proteina")
    sodium: float | None = Field(default=None, alias="sodio")

    def __init__(self, **data):
        # Convert string values to floats during initialization
        for key, value in data.items():
            if isinstance(value, str) and key != "calories" and key != "calorias":
                try:
                    cleaned = value.strip().lower()
                    for unit in ["g", "mg", "kcal", "kj"]:
                        cleaned = cleaned.replace(unit, "")
                    cleaned = cleaned.strip()
                    data[key] = float(cleaned) if cleaned else None
                except (ValueError, AttributeError):
                    data[key] = None
            elif key in ("calories", "calorias") and isinstance(value, str):
                try:
                    data[key] = float(value.strip()) if value.strip() else None
                except (ValueError, AttributeError):
                    data[key] = None
        super().__init__(**data)


class IdentifiedAdditives(BaseModel):
    """Identified additives categorized by type."""

    model_config = ConfigDict(populate_by_name=True)

    sweeteners: list[str] = Field(default=[], alias="endulcorantes")
    colorants: list[str] = Field(default=[], alias="colorantes")
    preservatives: list[str] = Field(default=[], alias="conservantes")
    flavorings: list[str] = Field(default=[], alias="saborizantes")


# Keep old name as alias for imports
AditivosIdentificados = IdentifiedAdditives


class ProductClassification(BaseModel):
    """Product classification based on processing level and risk."""

    model_config = ConfigDict(populate_by_name=True)

    processing_level: str = Field(alias="nivel_procesamiento")  # NOVA 1-4
    food_category: str | None = Field(default=None, alias="categoria_alimento")
    risk_category: str = Field(alias="categoria_riesgo")


# Keep old name as alias for imports
ClasificacionProducto = ProductClassification


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of the general score calculation."""

    model_config = ConfigDict(populate_by_name=True)

    base_points: int = Field(default=10, alias="puntos_base")
    nova4_processing: int | None = Field(default=None, alias="procesamiento_NOVA4")
    nova3_processing: int | None = Field(default=None, alias="procesamiento_NOVA3")
    high_added_sugars: int | None = Field(default=None, alias="azucares_anadidos_alto")
    moderate_added_sugars: int | None = Field(default=None, alias="azucares_anadidos_moderado")
    artificial_colorants: int | None = Field(default=None, alias="colorantes_artificiales")
    artificial_sweeteners: int | None = Field(default=None, alias="endulcorantes_artificiales")
    high_sodium: int | None = Field(default=None, alias="sodio_alto")
    moderate_sodium: int | None = Field(default=None, alias="sodio_moderado")
    high_saturated_fat: int | None = Field(default=None, alias="grasas_saturadas_alto")
    trans_fat: int | None = Field(default=None, alias="grasas_trans")
    low_nutrient_density: int | None = Field(default=None, alias="baja_densidad_nutricional")
    high_nutrient_density: int | None = Field(default=None, alias="alta_densidad_nutricional")
    high_fiber: int | None = Field(default=None, alias="fibra_alta")
    high_protein: int | None = Field(default=None, alias="proteina_alta")
    beneficial_components: int | None = Field(default=None, alias="componentes_beneficiosos")
    healthy_fats: int | None = Field(default=None, alias="grasas_saludables")
    controversial_preservatives: int | None = Field(default=None, alias="conservantes_controvertidos")
    artificial_flavorings: int | None = Field(default=None, alias="saborizantes_artificiales")
    multiple_additives: int | None = Field(default=None, alias="multiples_aditivos")
    vitamins_minerals: int | None = Field(default=None, alias="vitaminas_minerales")
    multiple_excess_adjustment: str | None = Field(default=None, alias="ajuste_multiples_excesos")


# Keep old name as alias for imports
DesgloseCalculo = ScoreBreakdown


class NutritionalEvaluation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    strengths: list[str] = Field(default=[], alias="fortalezas")
    weaknesses: list[str] = Field(default=[], alias="debilidades")
    warnings: list[str] = Field(default=[], alias="advertencias")
    reference_comparison: str | None = Field(default=None, alias="comparacion_referencia")


class Calification(BaseModel):
    """Simple qualification with score and justification."""

    model_config = ConfigDict(populate_by_name=True)

    score: float = Field(alias="puntuacion")
    justification: str = Field(alias="justificacion")

    def __init__(self, **data):
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        if "score" in data and isinstance(data["score"], str):
            try:
                data["score"] = float(data["score"].strip())
            except (ValueError, AttributeError):
                data["score"] = 0.0
        super().__init__(**data)


class GeneralRating(BaseModel):
    """General rating with detailed scoring breakdown."""

    model_config = ConfigDict(populate_by_name=True)

    score: float = Field(alias="puntuacion")
    score_breakdown: ScoreBreakdown | None = Field(default=None, alias="desglose_calculo")
    product_category: str | None = Field(default=None, alias="categoria_producto")
    processing_level: str | None = Field(default=None, alias="nivel_procesamiento")
    risk_category: str | None = Field(default=None, alias="categoria_riesgo")
    justification: str = Field(alias="justificacion")

    def __init__(self, **data):
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        if "score" in data and isinstance(data["score"], str):
            try:
                data["score"] = float(data["score"].strip())
            except (ValueError, AttributeError):
                data["score"] = 0.0
        super().__init__(**data)


# Keep old name as alias for imports
CalificacionGeneral = GeneralRating


class ProfileRating(BaseModel):
    """Detailed rating for a specific health profile."""

    model_config = ConfigDict(populate_by_name=True)

    score: float = Field(alias="puntuacion")
    recommended_frequency: str | None = Field(default=None, alias="frecuencia_recomendada")
    suggested_serving_size: str | None = Field(default=None, alias="tamano_porcion_sugerido")
    justification: str = Field(alias="justificacion")

    def __init__(self, **data):
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        if "score" in data and isinstance(data["score"], str):
            try:
                data["score"] = float(data["score"].strip())
            except (ValueError, AttributeError):
                data["score"] = 0.0
        super().__init__(**data)


# Keep old name as alias for imports
ProfileCalification = ProfileRating


class Recommendations(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    general_consumption: str | None = Field(default=None, alias="consumo_general")
    optimal_frequency: str | None = Field(default=None, alias="frecuencia_optima")
    suggested_alternatives: list[str] = Field(default=[], alias="alternativas_sugeridas")


class AIAnalysisResponse(BaseResponse):
    """Response model for AI analysis endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    analysis_id: str = Field(..., description="Unique identifier for this analysis")

    # Extracted information
    product: ProductInfo | None = Field(default=None, alias="producto")
    ingredients: list[str] = Field(default=[], alias="ingredientes")
    identified_allergens: list[str] = Field(default=[], alias="alergenos_identificados")
    identified_additives: IdentifiedAdditives | None = Field(default=None, alias="aditivos_identificados")
    nutritional_information: dict[str, PortionInfo] | None = Field(default=None, alias="informacion_nutricional")
    product_classification: ProductClassification | None = Field(default=None, alias="clasificacion_producto")
    general_rating: GeneralRating | None = Field(default=None, alias="calificacion_general")
    profile_ratings: dict[str, ProfileRating] = Field(default={}, alias="calificaciones")
    nutritional_evaluation: NutritionalEvaluation | None = Field(default=None, alias="evaluacion_nutricional")
    recommendations: Recommendations | None = Field(default=None, alias="recomendaciones")

    executive_summary: str | None = Field(default=None, alias="resumen_ejecutivo")

    # Metadata
    images_processed: int = Field(..., description="Number of images processed")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence in analysis")

    # AI model info
    model_used: str = Field(default="gpt-4o-mini")
    model_version: str | None = None

    # Token usage
    tokens_used: int | None = Field(default=None, description="Total tokens used in the API call")
    prompt_tokens: int | None = Field(default=None, description="Tokens used in the prompt")
    completion_tokens: int | None = Field(default=None, description="Tokens used in the completion")


class ImageProcessingError(BaseModel):
    """Error information for image processing issues."""

    image_index: int
    error_type: str
    error_message: str
    suggestion: str | None = None


class AIAnalysisErrorResponse(BaseResponse):
    """Error response for AI analysis failures."""

    success: bool = False
    error_type: str
    processing_errors: list[ImageProcessingError] | None = None
    partial_results: AIAnalysisResponse | None = None
