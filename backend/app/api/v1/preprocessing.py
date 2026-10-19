from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.schemas.preprocessing import (
    PreprocessRequest, PreprocessResult, PreviewRequest, PreviewResult, PreprocessItem,
)
from backend.app.services import preprocessing_service

router = APIRouter()

@router.post("/run", response_model=PreprocessResult)
def run(req: PreprocessRequest, db: Session = Depends(get_db)):
    items = preprocessing_service.preprocess_records(db, req.record_ids, req.limit, req.force)
    return {
        "processed": len(items),
        "items": [PreprocessItem(id=r.id, text=r.text, text_clean=r.text_clean or "") for r in items],
    }

@router.post("/preview", response_model=PreviewResult)
def preview(req: PreviewRequest):
    return preprocessing_service.preview(req.text)