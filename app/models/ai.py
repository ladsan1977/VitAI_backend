"""AI-related Pydantic models for request/response validation."""

from typing import Any

from pydantic import BaseModel, Field

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
    nombre: str | None = None
    marca: str | None = None
    tamano_porcion: str | None = None
    porciones_por_envase: str | None = None


class PortionInfo(BaseModel):
    calorias: float | None = None
    grasas_totales: float | None = None
    grasas_saturadas: float | None = None
    grasas_trans: float | None = None
    carbohidratos_totales: float | None = None
    fibra: float | None = None
    azucares_totales: float | None = None
    azucares_anadidos: float | None = None
    proteina: float | None = None
    sodio: float | None = None

    def __init__(self, **data):
        # Convert string values to floats during initialization
        for key, value in data.items():
            if isinstance(value, str) and key != "calorias":  # calorias is already float
                try:
                    # Remove common units and clean the string
                    cleaned = value.strip().lower()
                    for unit in ["g", "mg", "kcal", "kj"]:
                        cleaned = cleaned.replace(unit, "")
                    cleaned = cleaned.strip()
                    data[key] = float(cleaned) if cleaned else None
                except (ValueError, AttributeError):
                    data[key] = None
            elif key == "calorias" and isinstance(value, str):
                try:
                    data[key] = float(value.strip()) if value.strip() else None
                except (ValueError, AttributeError):
                    data[key] = None
        super().__init__(**data)


class AditivosIdentificados(BaseModel):
    """Identified additives categorized by type."""

    endulcorantes: list[str] = []
    colorantes: list[str] = []
    conservantes: list[str] = []
    saborizantes: list[str] = []


class ClasificacionProducto(BaseModel):
    """Product classification based on processing level and risk."""

    nivel_procesamiento: str  # NOVA 1-4
    categoria_alimento: str | None = None
    categoria_riesgo: str  # Alto/moderado/bajo riesgo


class DesgloseCalculo(BaseModel):
    """Detailed breakdown of the general score calculation."""

    puntos_base: int = 10
    procesamiento_NOVA4: int | None = None
    procesamiento_NOVA3: int | None = None
    azucares_anadidos_alto: int | None = None
    azucares_anadidos_moderado: int | None = None
    colorantes_artificiales: int | None = None
    endulcorantes_artificiales: int | None = None
    sodio_alto: int | None = None
    sodio_moderado: int | None = None
    grasas_saturadas_alto: int | None = None
    grasas_trans: int | None = None
    baja_densidad_nutricional: int | None = None
    alta_densidad_nutricional: int | None = None
    fibra_alta: int | None = None
    proteina_alta: int | None = None
    componentes_beneficiosos: int | None = None
    grasas_saludables: int | None = None
    conservantes_controvertidos: int | None = None
    saborizantes_artificiales: int | None = None
    multiples_aditivos: int | None = None
    vitaminas_minerales: int | None = None
    ajuste_multiples_excesos: str | None = None


class NutritionalEvaluation(BaseModel):
    fortalezas: list[str] = []
    debilidades: list[str] = []
    advertencias: list[str] = []
    comparacion_referencia: str | None = None


class Calification(BaseModel):
    """Simple qualification with score and justification."""

    puntuacion: float
    justificacion: str

    def __init__(self, **data):
        # Convert puntuacion to float if it's a string
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        super().__init__(**data)


class CalificacionGeneral(BaseModel):
    """General qualification with detailed scoring breakdown."""

    puntuacion: float
    desglose_calculo: DesgloseCalculo | None = None
    categoria_producto: str | None = None
    nivel_procesamiento: str | None = None
    categoria_riesgo: str | None = None
    justificacion: str

    def __init__(self, **data):
        # Convert puntuacion to float if it's a string
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        super().__init__(**data)


class ProfileCalification(BaseModel):
    """Detailed qualification for a specific health profile."""

    puntuacion: float
    frecuencia_recomendada: str | None = None
    tamano_porcion_sugerido: str | None = None
    justificacion: str

    def __init__(self, **data):
        # Convert puntuacion to float if it's a string
        if "puntuacion" in data and isinstance(data["puntuacion"], str):
            try:
                data["puntuacion"] = float(data["puntuacion"].strip())
            except (ValueError, AttributeError):
                data["puntuacion"] = 0.0
        super().__init__(**data)


class Recommendations(BaseModel):
    consumo_general: str | None = None
    frecuencia_optima: str | None = None
    alternativas_sugeridas: list[str] = []


class AIAnalysisResponse(BaseResponse):
    """Response model for AI analysis endpoint."""

    analysis_id: str = Field(..., description="Unique identifier for this analysis")

    # Extracted information
    producto: ProductInfo | None = None
    ingredientes: list[str] = []
    alergenos_identificados: list[str] = []
    aditivos_identificados: AditivosIdentificados | None = None
    informacion_nutricional: dict[str, PortionInfo] | None = None  # por_porcion
    clasificacion_producto: ClasificacionProducto | None = None
    calificacion_general: CalificacionGeneral | None = None
    calificaciones: dict[str, ProfileCalification] = {}
    evaluacion_nutricional: NutritionalEvaluation | None = None
    recomendaciones: Recommendations | None = None

    resumen_ejecutivo: str | None = None

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
