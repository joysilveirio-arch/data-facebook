from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

VALID_LABELS = {"positive", "negative", "neutral"}

class LabelIn(BaseModel):
    label: str = Field(..., pattern="^(positive|negative|neutral)$")
    labeled_by: Optional[str] = "admin"

class LabelOut(BaseModel):
    id: int
    record_id: int
    label: str
    labeled_by: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class BulkLabelItem(BaseModel):
    id: int
    label: str = Field(..., pattern="^(positive|negative|neutral)$")

class BulkLabelIn(BaseModel):
    items: List[BulkLabelItem]
    labeled_by: Optional[str] = "admin"

class LabelStats(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    unlabeled: int = 0