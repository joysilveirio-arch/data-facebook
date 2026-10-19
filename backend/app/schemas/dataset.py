from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DatasetBase(BaseModel):
    name: str
    source_file: Optional[str] = None
    format: Optional[str] = "csv"
    description: Optional[str] = None

class DatasetCreate(DatasetBase):
    pass

class DatasetOut(DatasetBase):
    id: int
    total_records: int
    is_active: bool
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ImportRequest(BaseModel):
    file_path: str = Field(..., description="Path relatif ke backend/data/ atau absolut")
    format: Optional[str] = "csv"
    reset: Optional[bool] = False
    dataset_name: Optional[str] = None
    description: Optional[str] = None

class ImportResult(BaseModel):
    imported: int
    skipped: int
    total_now: int
    dataset_id: Optional[int] = None