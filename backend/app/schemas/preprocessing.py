from pydantic import BaseModel
from typing import List, Optional

class PreprocessRequest(BaseModel):
    record_ids: Optional[List[int]] = None
    limit: Optional[int] = None
    force: Optional[bool] = False

class PreprocessItem(BaseModel):
    id: int
    text: str
    text_clean: str

class PreprocessResult(BaseModel):
    processed: int
    items: List[PreprocessItem]

class PreviewRequest(BaseModel):
    text: str

class PreviewResult(BaseModel):
    original: str
    clean: str