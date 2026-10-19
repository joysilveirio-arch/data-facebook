from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.schemas.prediction import (
    PredictRequest, PredictOut, PredictBatchRequest, PredictBatchOut,
)
from backend.app.services import prediction_service

router = APIRouter()

@router.post("/", response_model=PredictOut)
def predict(req: PredictRequest):
    return prediction_service.predict_one(req.text)

@router.post("/batch", response_model=PredictBatchOut)
def predict_batch(req: PredictBatchRequest):
    return prediction_service.predict_batch(req.texts)

@router.post("/apply/{record_id}")
def apply_one(record_id: int, db: Session = Depends(get_db)):
    return prediction_service.apply_prediction_to_record(db, record_id)

@router.post("/apply-all")
def apply_all(limit: int = 0, db: Session = Depends(get_db)):
    return prediction_service.apply_all(db, limit)