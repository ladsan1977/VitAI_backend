"""AI consumption metrics ORM model for tracking OpenAI API usage."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class AiConsumptionMetric(Base, TimestampMixin):
    """
    AI consumption metrics model for tracking OpenAI API costs and token usage.

    Stores per-request metrics for AI analysis calls including
    token counts, costs, response times, and cache hits.
    """

    __tablename__ = "ai_consumption_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    openai_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<AiConsumptionMetric(id={self.id}, cache_hit={self.cache_hit}, tokens={self.tokens_used})>"
