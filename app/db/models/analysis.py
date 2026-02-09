"""Analysis ORM model for storing AI analysis results."""

import uuid

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin


class Analysis(Base, TimestampMixin):
    """
    Analysis model for storing product nutrition analysis results.

    Stores complete AI analysis with deduplication via image hash.
    """

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    image_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analysis_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, product={self.product_name}, type={self.analysis_type})>"
