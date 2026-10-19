
import json
import logging

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    ModelNotTrainedError,
    NotFoundError,
)
from backend.app.ml.pipeline import ml_pipeline
from backend.app.models.prediction_history import PredictionHistory
from backend.app.models.text_record import TextRecord


logger = logging.getLogger(__name__)

VALID_LABELS = {"positive", "negative", "neutral"}


def predict_one(text: str) -> dict:
    """Halo predisaun sentiment ba testu ida."""
    try:
        result = ml_pipeline.predict_one(text or "")
    except RuntimeError as exc:
        raise ModelNotTrainedError(str(exc)) from exc

    if not isinstance(result, dict) or "label" not in result:
        raise RuntimeError(
            "Model pipeline tenke retorna dictionary ho chave 'label'."
        )

    label = str(result["label"]).strip().lower()

    if label not in VALID_LABELS:
        raise RuntimeError(
            f"Sentiment label la válidu: {label!r}. "
            f"Label permitidu: {sorted(VALID_LABELS)}"
        )

    return {**result, "label": label}


def predict_batch(texts: list[str]) -> dict:
    """Halo predisaun ba lista testu."""
    try:
        results = ml_pipeline.predict_many(texts)
    except RuntimeError as exc:
        raise ModelNotTrainedError(str(exc)) from exc

    return {"results": results}


def _save_prediction(
    db: Session,
    record: TextRecord,
    result: dict,
) -> None:
    """Grava predisaun tuir koluna PredictionHistory."""

    probabilities = result.get("probabilities") or {}

    prediction = PredictionHistory(
        record_id=record.id,
        input_text=(record.text or "")[:2000],
        cleaned_text=result.get("clean"),
        predicted_label=str(result["label"]).strip().lower(),
        probability_json=json.dumps(
            probabilities,
            ensure_ascii=False,
        ),
    )

    db.add(prediction)


def apply_prediction_to_record(
    db: Session,
    record_id: int,
) -> dict:
    """Prediz sentiment ba record ida no grava ba database."""

    record = (
        db.query(TextRecord)
        .filter(TextRecord.id == record_id)
        .first()
    )

    if record is None:
        raise NotFoundError("Record la hetan.")

    result = predict_one(record.text or "")

    try:
        _save_prediction(db, record, result)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "La konsege grava predisaun ba record_id=%s",
            record_id,
        )
        raise

    return {"id": record.id, **result}


def apply_all(db: Session, limit: int = 0) -> dict:
    """Prediz sentiment ba records no grava rezultadu hotu."""

    query = db.query(TextRecord).order_by(TextRecord.id.asc())

    if limit > 0:
        query = query.limit(limit)

    records = query.all()

    if not records:
        return {
            "updated": 0,
            "message": "La iha record atu halo predisaun.",
        }

    updated = 0

    try:
        for record in records:
            result = predict_one(record.text or "")
            _save_prediction(db, record, result)
            updated += 1

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Predisaun ba records hotu falla.")
        raise

    return {
        "updated": updated,
        "message": f"Predisaun kompletu ba {updated} records.",
    }
