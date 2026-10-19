from sqlalchemy import Column, String, Integer, Text, DateTime
from backend.app.models.base import BaseModel

class PreprocessingJob(BaseModel):
    __tablename__ = "preprocessing_jobs"

    status = Column(String(20), default="pending")  # pending|running|done|failed
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<PreprocessingJob id={self.id} status={self.status}>"