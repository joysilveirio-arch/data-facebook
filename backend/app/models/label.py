from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class Label(BaseModel):
    __tablename__ = "labels"

    record_id = Column(Integer, ForeignKey("text_records.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(20), nullable=False, index=True)  # positive|negative|neutral
    labeled_by = Column(String(100), default="admin")

    record = relationship("TextRecord", back_populates="labels")

    def __repr__(self) -> str:
        return f"<Label id={self.id} record_id={self.record_id} label={self.label}>"