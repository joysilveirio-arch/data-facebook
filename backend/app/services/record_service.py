
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.app.core.exceptions import NotFoundError
from backend.app.models.dataset import Dataset
from backend.app.models.text_record import TextRecord
from backend.app.schemas.record import RecordCreate, RecordUpdate


class RecordConflictError(Exception):
    """Record ID duplicate ka konflitu ho database."""


def list_records(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    label: str | None = None,
    predicted_label: str | None = None,
    dataset_id: int | None = None,
) -> dict:
    query = db.query(TextRecord).options(
        selectinload(TextRecord.labels),
        selectinload(TextRecord.predictions),
    )

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                TextRecord.text.ilike(term),
                TextRecord.author_name.ilike(term),
                TextRecord.comment_id.ilike(term),
                TextRecord.post_title.ilike(term),
            )
        )

    if dataset_id is not None:
        query = query.filter(TextRecord.dataset_id == dataset_id)

    if label:
        from backend.app.models.label import Label

        query = query.filter(
            TextRecord.id.in_(
                db.query(Label.record_id).filter(Label.label == label.lower())
            )
        )

    if predicted_label:
        from backend.app.models.prediction_history import PredictionHistory

        query = query.filter(
            TextRecord.id.in_(
                db.query(PredictionHistory.record_id).filter(
                    PredictionHistory.predicted_label == predicted_label.lower()
                )
            )
        )

    total = query.count()

    items = (
        query.order_by(TextRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def get_record(db: Session, record_id: int) -> TextRecord:
    record = (
        db.query(TextRecord)
        .options(
            selectinload(TextRecord.labels),
            selectinload(TextRecord.predictions),
        )
        .filter(TextRecord.id == record_id)
        .first()
    )

    if record is None:
        raise NotFoundError(f"Record ID {record_id} la hetan.")
    return record


def create_record(db: Session, payload: RecordCreate) -> TextRecord:
    data = payload.model_dump()

    dataset_id = data.get("dataset_id")
    if dataset_id is not None:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset is None:
            raise NotFoundError(f"Dataset ID {dataset_id} la hetan.")

    record = TextRecord(**data)
    db.add(record)

    try:
        db.flush()

        if dataset_id is not None:
            dataset.total_records = (
                db.query(TextRecord)
                .filter(TextRecord.dataset_id == dataset_id)
                .count()
            )

        db.commit()
        db.refresh(record)
        return record

    except IntegrityError as exc:
        db.rollback()
        raise RecordConflictError(
            "comment_id ne'e eziste ona. Uza ID diferente."
        ) from exc

    except Exception:
        db.rollback()
        raise


def update_record(
    db: Session,
    record_id: int,
    payload: RecordUpdate,
) -> TextRecord:
    record = get_record(db, record_id)
    old_dataset_id = record.dataset_id

    changes = payload.model_dump(exclude_unset=True)

    for key, value in changes.items():
        if key == "dataset_id" and value is not None:
            dataset = db.query(Dataset).filter(Dataset.id == value).first()
            if dataset is None:
                raise NotFoundError(f"Dataset ID {value} la hetan.")

        setattr(record, key, value)

    try:
        db.flush()

        dataset_ids = {
            dataset_id
            for dataset_id in (old_dataset_id, record.dataset_id)
            if dataset_id is not None
        }

        for dataset_id in dataset_ids:
            dataset = (
                db.query(Dataset)
                .filter(Dataset.id == dataset_id)
                .first()
            )
            if dataset:
                dataset.total_records = (
                    db.query(TextRecord)
                    .filter(TextRecord.dataset_id == dataset_id)
                    .count()
                )

        db.commit()
        db.refresh(record)
        return record

    except IntegrityError as exc:
        db.rollback()
        raise RecordConflictError(
            "comment_id ne'e uza ona husi record seluk."
        ) from exc

    except Exception:
        db.rollback()
        raise


def delete_record(db: Session, record_id: int) -> None:
    record = get_record(db, record_id)
    dataset_id = record.dataset_id

    try:
        db.delete(record)
        db.flush()

        if dataset_id is not None:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.total_records = (
                    db.query(TextRecord)
                    .filter(TextRecord.dataset_id == dataset_id)
                    .count()
                )

        db.commit()

    except Exception:
        db.rollback()
        raise
