from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.schemas.common import PageOut
from backend.app.schemas.record import RecordOut
from backend.app.schemas.label import LabelIn, LabelOut, BulkLabelIn, LabelStats
from backend.app.services import labeling_service

router = APIRouter()

@router.post("/{record_id}", response_model=LabelOut)
def label_one(record_id: int, payload: LabelIn, db: Session = Depends(get_db)):
    return labeling_service.label_record(db, record_id, payload.label, payload.labeled_by or "admin")

@router.post("/bulk")
def bulk(payload: BulkLabelIn, db: Session = Depends(get_db)):
    n = labeling_service.bulk_label(db, [it.model_dump() for it in payload.items], payload.labeled_by or "admin")
    return {"updated": n}

@router.delete("/{record_id}")
def unlabel(record_id: int, db: Session = Depends(get_db)):
    n = labeling_service.unlabel(db, record_id)
    return {"unlabeled": n}

@router.get("/unlabeled", response_model=PageOut[RecordOut])
def unlabeled(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return labeling_service.unlabeled_records(db, page, page_size)

@router.get("/stats", response_model=LabelStats)
def stats(db: Session = Depends(get_db)):
    return labeling_service.label_stats(db)