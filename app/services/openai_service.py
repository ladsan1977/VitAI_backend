"""OpenAI service for AI-powered nutritional analysis."""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import settings
from ..core.exceptions import AnalysisValidationError, OpenAIServiceError
from ..models.ai import (
    AditivosIdentificados,
    AIAnalysisResponse,
    CalificacionGeneral,
    ClasificacionProducto,
    DesgloseCalculo,
    NutritionalEvaluation,
    PortionInfo,
    ProductInfo,
    ProfileCalification,
    Recommendations,
)

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
    ) -> AIAnalysisResponse:
        """Analyze nutrition information from product images."""
        start_time = datetime.now(UTC)
        analysis_id = str(uuid.uuid4())

        try:
            # Build prompt
            prompt = self._build_analysis_prompt(analysis_type, user_profile, dietary_preferences, health_conditions)

            # Prepare images
            image_messages = self._prepare_image_messages(images)

            # Make real API call
            response_data, token_usage = await self._real_openai_call(prompt, image_messages, analysis_type)

            # Parse and validate
            analysis_response = self._parse_openai_response(
                response_data, analysis_id, len(images), start_time, token_usage
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
    ) -> str:
        """Build the analysis prompt for OpenAI using external markdown file."""
        try:
            # Ruta del prompt
            prompt_path = Path(__file__).parent / "prompts" / "prompt_produccion_nutricional_v2.md"

            # Cargar el contenido si no está en cache
            if self.prompt_cache is None:
                if not prompt_path.exists():
                    raise FileNotFoundError(f"Prompt file not found at: {prompt_path}")
                self.prompt_cache = prompt_path.read_text(encoding="utf-8")

            base_prompt = self.prompt_cache

            # Foco del análisis
            if analysis_type == "nutrition":
                focus_section = (
                    "⚙️ Foco del análisis: Prioriza la extracción de datos nutricionales y valores por porción."
                )
            elif analysis_type == "ingredients":
                focus_section = "⚙️ Foco del análisis: Prioriza lista de ingredientes, alérgenos y aditivos."
            else:
                focus_section = "⚙️ Foco del análisis: Proporciona un análisis completo: nutrición, ingredientes y evaluación integral de salud."

            # Personalización del análisis
            personalization = ""
            if dietary_preferences or health_conditions or user_profile:
                personalization += "\n\n## 📌 Personalización del análisis\n"
                if dietary_preferences:
                    personalization += f"- Preferencias dietéticas: {', '.join(dietary_preferences)}\n"
                if health_conditions:
                    personalization += f"- Condiciones de salud a considerar: {', '.join(health_conditions)}\n"
                if user_profile:
                    personalization += f"- Perfil del usuario: {json.dumps(user_profile, ensure_ascii=False)}\n"

            # Prompt final ensamblado
            full_prompt = f"{base_prompt}\n\n{focus_section}\n{personalization}"

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
                                "Eres un analista nutricional experto. "
                                "Debes seguir exactamente los pasos y reglas del prompt. "
                                "No ignores ninguna condición de coherencia entre puntuaciones. "
                                "Si la calificación_general es menor que 5, ninguna puntuación individual puede ser mayor que 7. "
                                "Devuelve únicamente un JSON válido, sin texto adicional ni explicación fuera del JSON."
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
                text={"format": {"type": "text"}},
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
    # Parseo de respuesta
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

            # ---------- Producto ----------
            logger.debug("Parsing producto...")
            producto = (
                ProductInfo(
                    nombre=response_data.get("producto", {}).get("nombre"),
                    marca=response_data.get("producto", {}).get("marca"),
                    tamano_porcion=response_data.get("producto", {}).get("tamano_porcion"),
                    porciones_por_envase=response_data.get("producto", {}).get("porciones_por_envase"),
                )
                if "producto" in response_data
                else None
            )
            logger.debug(f"Producto parsed: {producto is not None}")

            # ---------- Ingredientes ----------
            logger.debug("Parsing ingredientes...")
            ingredientes = response_data.get("ingredientes", [])
            logger.debug(f"Ingredientes count: {len(ingredientes)}")

            # ---------- Alergenos identificados ----------
            alergenos_identificados = response_data.get("alergenos_identificados", [])

            # ---------- Aditivos identificados ----------
            aditivos_identificados = None
            if "aditivos_identificados" in response_data:
                adit_data = response_data["aditivos_identificados"]
                aditivos_identificados = AditivosIdentificados(
                    endulcorantes=adit_data.get("endulcorantes", []),
                    colorantes=adit_data.get("colorantes", []),
                    conservantes=adit_data.get("conservantes", []),
                    saborizantes=adit_data.get("saborizantes", []),
                )

            # ---------- Información nutricional ----------
            informacion_nutricional = None
            if "informacion_nutricional" in response_data:
                porcion_data = response_data["informacion_nutricional"].get("por_porcion", {})
                informacion_nutricional = {"por_porcion": PortionInfo(**porcion_data)}

            # ---------- Clasificacion producto ----------
            clasificacion_producto = None
            if "clasificacion_producto" in response_data:
                clasif_data = response_data["clasificacion_producto"]
                clasificacion_producto = ClasificacionProducto(
                    nivel_procesamiento=clasif_data.get("nivel_procesamiento", ""),
                    categoria_alimento=clasif_data.get("categoria_alimento"),
                    categoria_riesgo=clasif_data.get("categoria_riesgo", ""),
                )

            # ---------- Evaluación nutricional ----------
            evaluacion_nutricional = None
            if "evaluacion_nutricional" in response_data:
                eval_data = response_data["evaluacion_nutricional"]
                evaluacion_nutricional = NutritionalEvaluation(
                    fortalezas=eval_data.get("fortalezas", []),
                    debilidades=eval_data.get("debilidades", []),
                    advertencias=eval_data.get("advertencias", []),
                    comparacion_referencia=eval_data.get("comparacion_referencia"),
                )

            # ---------- Calificaciones individuales ----------
            logger.debug("Parsing calificaciones...")
            calificaciones = {}
            if "calificaciones" in response_data:
                logger.debug(f"Found calificaciones with profiles: {list(response_data['calificaciones'].keys())}")
                for perfil, data in response_data["calificaciones"].items():
                    try:
                        logger.debug(f"Parsing profile: {perfil}")

                        calificaciones[perfil] = ProfileCalification(
                            puntuacion=data.get("puntuacion"),
                            frecuencia_recomendada=data.get("frecuencia_recomendada"),
                            tamano_porcion_sugerido=data.get("tamano_porcion_sugerido"),
                            justificacion=data.get("justificacion", ""),
                        )
                        logger.debug(f"Successfully parsed profile: {perfil}")
                    except Exception as e:
                        logger.error(f"Error parsing profile {perfil}: {str(e)}", exc_info=True)
                        continue
            logger.debug(f"Total calificaciones parsed: {len(calificaciones)}")

            # ---------- Calificación general (nuevo campo) ----------
            logger.debug("Parsing calificacion_general...")
            calificacion_general = None
            if "calificacion_general" in response_data:
                cg_data = response_data["calificacion_general"]
                logger.debug(f"calificacion_general keys: {list(cg_data.keys())}")

                # Parse desglose_calculo if present
                desglose_calculo = None
                if "desglose_calculo" in cg_data:
                    logger.debug("Parsing desglose_calculo...")
                    dc_data = cg_data["desglose_calculo"]
                    desglose_calculo = DesgloseCalculo(**dc_data)
                    logger.debug("desglose_calculo parsed successfully")

                calificacion_general = CalificacionGeneral(
                    puntuacion=cg_data.get("puntuacion"),
                    desglose_calculo=desglose_calculo,
                    categoria_producto=cg_data.get("categoria_producto"),
                    nivel_procesamiento=cg_data.get("nivel_procesamiento"),
                    categoria_riesgo=cg_data.get("categoria_riesgo"),
                    justificacion=cg_data.get("justificacion", ""),
                )
                logger.debug("calificacion_general parsed successfully")

            # ---------- Recomendaciones ----------
            recomendaciones = None
            if "recomendaciones" in response_data:
                rec_data = response_data["recomendaciones"]
                recomendaciones = Recommendations(
                    consumo_general=rec_data.get("consumo_general"),
                    frecuencia_optima=rec_data.get("frecuencia_optima"),
                    contraindicado_para=rec_data.get("contraindicado_para", []),
                    alternativas_sugeridas=rec_data.get("alternativas_sugeridas", []),
                    como_mejorar_eleccion=rec_data.get("como_mejorar_eleccion", []),
                )

            # ---------- Resumen ejecutivo ----------
            resumen_ejecutivo = response_data.get("resumen_ejecutivo")

            # ---------- Confidence score ----------
            confidence_score = float(response_data.get("confidence_score", 0.5))

            # ---------- Construcción de respuesta ----------
            logger.debug("Constructing AIAnalysisResponse...")
            response = AIAnalysisResponse(
                analysis_id=analysis_id,
                producto=producto,
                ingredientes=ingredientes,
                alergenos_identificados=alergenos_identificados,
                aditivos_identificados=aditivos_identificados,
                informacion_nutricional=informacion_nutricional,
                clasificacion_producto=clasificacion_producto,
                calificacion_general=calificacion_general,
                calificaciones=calificaciones,
                evaluacion_nutricional=evaluacion_nutricional,
                recomendaciones=recomendaciones,
                resumen_ejecutivo=resumen_ejecutivo,
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
