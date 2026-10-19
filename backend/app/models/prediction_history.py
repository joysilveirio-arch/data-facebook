"""Log of prediction calls."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int | None] = mapped_column(
        ForeignKey("text_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    predicted_label: Mapped[str] = mapped_column(String(64), nullable=False)
    probability_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    record: Mapped["TextRecord"] = relationship("TextRecord", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<PredictionHistory id={self.id} label={self.predicted_label!r}>"