from sqlalchemy import Column, String, Text, Integer, Boolean
from sqlalchemy.orm import relationship

from backend.app.models.base import BaseModel


class Dataset(BaseModel):
    __tablename__ = "datasets"

    name = Column(String(255), nullable=False, unique=True, index=True)
    source_file = Column(String(500), nullable=True)
    format = Column(String(20), default="csv")
    description = Column(Text, nullable=True)
    total_records = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    records = relationship(
        "TextRecord",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Dataset id={self.id} "
            f"name={self.name} records={self.total_records}>"
        )