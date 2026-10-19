from pydantic import BaseModel
from typing import List, Dict

class PredictRequest(BaseModel):
    text: str

class PredictBatchRequest(BaseModel):
    texts: List[str]

class PredictOut(BaseModel):
    text: str
    clean: str
    label: str
    confidence: float
    probabilities: Dict[str, float]

class PredictBatchOut(BaseModel):
    results: List[PredictOut]