
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.text_record import TextRecord
from backend.app.models.label import Label
from backend.app.models.prediction_history import PredictionHistory


SENTIMENT_LABELS = ("positive", "negative", "neutral")


def overview(db: Session) -> dict:
    """Kalkula estatistika husi dadus reais iha database."""

    # 1. Total records
    total = (
        db.query(func.count(TextRecord.id)).scalar() or 0
    )

    # 2. Total records ho label manual, konta record ida deit.
    labeled = (
        db.query(func.count(func.distinct(Label.record_id)))
        .filter(Label.record_id.isnot(None))
        .scalar()
        or 0
    )

    # 3. Total records ne'ebé iha predisaun AI ikus liu.
    latest_prediction_ids = (
        db.query(
            func.max(PredictionHistory.id).label("prediction_id")
        )
        .filter(PredictionHistory.record_id.isnot(None))
        .group_by(PredictionHistory.record_id)
        .subquery()
    )

    predicted = (
        db.query(func.count(PredictionHistory.record_id))
        .join(
            latest_prediction_ids,
            PredictionHistory.id
            == latest_prediction_ids.c.prediction_id,
        )
        .scalar()
        or 0
    )

    # 4. Average likes
    avg_value = (
        db.query(func.avg(TextRecord.likes_count)).scalar()
    )
    avg_likes = float(avg_value) if avg_value is not None else 0.0

    # 5. Distribuisaun label manual.
    latest_label_ids = (
        db.query(func.max(Label.id).label("label_id"))
        .filter(Label.record_id.isnot(None))
        .group_by(Label.record_id)
        .subquery()
    )

    label_rows = (
        db.query(
            func.lower(func.trim(Label.label)),
            func.count(Label.id),
        )
        .join(
            latest_label_ids,
            Label.id == latest_label_ids.c.label_id,
        )
        .group_by(func.lower(func.trim(Label.label)))
        .all()
    )

    dist_label = {label: 0 for label in SENTIMENT_LABELS}

    for label, count in label_rows:
        if label in dist_label:
            dist_label[label] = int(count)

    # 6. Distribuisaun predisaun AI.
    prediction_rows = (
        db.query(
            func.lower(func.trim(PredictionHistory.predicted_label)),
            func.count(PredictionHistory.id),
        )
        .join(
            latest_prediction_ids,
            PredictionHistory.id
            == latest_prediction_ids.c.prediction_id,
        )
        .group_by(
            func.lower(func.trim(PredictionHistory.predicted_label))
        )
        .all()
    )

    dist_pred = {label: 0 for label in SENTIMENT_LABELS}

    for label, count in prediction_rows:
        if label in dist_pred:
            dist_pred[label] = int(count)

    # 7. Top 10 authors
    normalized_author = func.coalesce(
        func.nullif(func.trim(TextRecord.author_name), ""),
        "Unknown",
    )

    author_rows = (
        db.query(
            normalized_author.label("author_name"),
            func.count(TextRecord.id).label("record_count"),
        )
        .group_by(normalized_author)
        .order_by(
            func.count(TextRecord.id).desc(),
            normalized_author.asc(),
        )
        .limit(10)
        .all()
    )

    top_authors = [
        {"author_name": name, "count": int(count)}
        for name, count in author_rows
    ]

    # 8. Daily record counts
    date_only = func.substr(TextRecord.date, 1, 10)

    daily_rows = (
        db.query(
            date_only.label("day"),
            func.count(TextRecord.id).label("record_count"),
        )
        .filter(TextRecord.date.isnot(None))
        .filter(func.trim(TextRecord.date) != "")
        .group_by(date_only)
        .order_by(date_only.desc())
        .limit(30)
        .all()
    )

    daily = [
        {"date": str(day), "count": int(count)}
        for day, count in reversed(daily_rows)
        if day is not None
    ]

    return {
        "total_records": int(total),
        "total_labeled": int(labeled),
        "total_predicted": int(predicted),
        "distribution_label": dist_label,
        "distribution_predicted": dist_pred,
        "top_authors": top_authors,
        "daily_counts": daily,
        "avg_likes": round(avg_likes, 4),
    }
