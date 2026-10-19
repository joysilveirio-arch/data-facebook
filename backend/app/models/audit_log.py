from sqlalchemy import Column, String, Integer, Text
from backend.app.models.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    actor = Column(String(100), default="system")
    action = Column(String(100), nullable=False, index=True)  # import|preprocess|label|train|predict
    entity = Column(String(50), nullable=True)                # dataset|record|model
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action}>"