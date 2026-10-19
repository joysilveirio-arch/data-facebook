
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.core.exceptions import NotFoundError
from backend.app.schemas.common import PageOut
from backend.app.schemas.record import RecordCreate, RecordOut, RecordUpdate
from backend.app.services import record_service

router = APIRouter()


@router.get("/", response_model=PageOut[RecordOut])
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: Optional[str] = Query(default=None, max_length=200),
    label: Optional[str] = Query(default=None),
    predicted_label: Optional[str] = Query(default=None),
    dataset_id: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    return record_service.list_records(
        db,
        page=page,
        page_size=page_size,
        q=q,
        label=label,
        predicted_label=predicted_label,
        dataset_id=dataset_id,
    )


@router.post("/", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    try:
        return record_service.create_record(db, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except record_service.RecordConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{record_id}", response_model=RecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    try:
        return record_service.get_record(db, record_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{record_id}", response_model=RecordOut)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
):
    try:
        return record_service.update_record(db, record_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except record_service.RecordConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    try:
        record_service.delete_record(db, record_id)
        return {"deleted": True, "id": record_id}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
