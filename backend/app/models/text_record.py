
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.models.base import BaseModel


class TextRecord(BaseModel):
    __tablename__ = "text_records"

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    comment_id = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    text = Column(Text, nullable=False)
    text_clean = Column(Text, nullable=True)

    author_name = Column(String(255), nullable=True, index=True)
    author_id = Column(String(100), nullable=True, index=True)
    post_title = Column(Text, nullable=True)
    date = Column(String(50), nullable=True, index=True)

    likes_count = Column(Integer, default=0)
    source_url = Column(String(1000), nullable=True)

    dataset = relationship(
        "Dataset",
        back_populates="records",
    )

    labels = relationship(
        "Label",
        back_populates="record",
        cascade="all, delete-orphan",
    )

    predictions = relationship(
        "PredictionHistory",
        back_populates="record",
        cascade="all, delete-orphan",
    )

    @property
    def latest_label(self):
        if not self.labels:
            return None

        return max(
            self.labels,
            key=lambda label: label.created_at,
        )

    @property
    def latest_prediction(self):
        if not self.predictions:
            return None

        return max(
            self.predictions,
            key=lambda prediction: prediction.created_at,
        )

    def __repr__(self) -> str:
        return (
            f"<TextRecord id={self.id} "
            f"comment_id={self.comment_id}>"
        )
