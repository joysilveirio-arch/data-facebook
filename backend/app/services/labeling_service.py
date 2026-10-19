
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    NotFoundError,
    ValidationError,
)
from backend.app.models.label import Label
from backend.app.models.text_record import TextRecord
from backend.app.schemas.label import VALID_LABELS


def label_record(
    db: Session,
    record_id: int,
    label: str,
    labeled_by: str = "admin",
) -> Label:
    # Validate label
    if label not in VALID_LABELS:
        raise ValidationError(
            f"Label harus salah satu dari {VALID_LABELS}"
        )

    # Find record using SQLAlchemy 2.x-compatible API
    record = db.get(TextRecord, record_id)

    if record is None:
        raise NotFoundError("Record tidak ditemukan")

    new_label = Label(
        record_id=record.id,
        label=label,
        labeled_by=labeled_by,
    )

    db.add(new_label)
    db.commit()
    db.refresh(new_label)

    return new_label


def bulk_label(
    db: Session,
    items: list[dict],
    labeled_by: str = "admin",
) -> int:
    updated = 0

    for item in items:
        record_id = item.get("id")
        label = item.get("label")

        if not record_id or label not in VALID_LABELS:
            continue

        record = db.get(TextRecord, record_id)

        if record is None:
            continue

        new_label = Label(
            record_id=record.id,
            label=label,
            labeled_by=labeled_by,
        )

        db.add(new_label)
        updated += 1

    db.commit()

    return updated


def unlabel(db: Session, record_id: int) -> int:
    deleted_count = (
        db.query(Label)
        .filter(Label.record_id == record_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count


def unlabeled_records(
    db: Session,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    # Exclude records that already have labels
    labeled_stmt = select(Label.record_id)

    query = db.query(TextRecord).filter(
        ~TextRecord.id.in_(labeled_stmt)
    )

    total = query.count()

    items = (
        query.order_by(TextRecord.id.asc())
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


def label_stats(db: Session) -> dict:
    counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
    }

    label_rows = (
        db.query(Label.label, func.count(Label.id))
        .group_by(Label.label)
        .all()
    )

    for label, count in label_rows:
        if label in counts:
            counts[label] = count

    # Count records without any label
    labeled_stmt = select(Label.record_id)

    unlabeled = (
        db.query(func.count(TextRecord.id))
        .filter(~TextRecord.id.in_(labeled_stmt))
        .scalar()
        or 0
    )

    counts["unlabeled"] = unlabeled

    return counts


def get_latest_label(
    db: Session,
    record_id: int,
) -> Label | None:
    return (
        db.query(Label)
        .filter(Label.record_id == record_id)
        .order_by(
            Label.created_at.desc(),
            Label.id.desc(),
        )
        .first()
    )
