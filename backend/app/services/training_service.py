from collections import Counter
from datetime import datetime, timezone
import json
import math

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ValidationError
from backend.app.ml.pipeline import ml_pipeline
from backend.app.models.label import Label
from backend.app.models.text_record import TextRecord
from backend.app.models.model_version import ModelVersion


VALID_LABELS = {"negative", "neutral", "positive"}

REQUIRED_METRICS = (
    "n_samples",
    "n_train",
    "n_test",
    "n_classes",
    "feature_count",
    "accuracy",
    "f1_macro",
    "precision_macro",
    "recall_macro",
    "confusion_matrix",
    "classes",
)


def _latest_label_map(db: Session) -> dict[int, str]:
    """
    Hetan label ikus ba kada record.
    Label foun liu mak uza, maski label ne'e mamuk.
    """
    rows = (
        db.query(Label.record_id, Label.label, Label.created_at, Label.id)
        .order_by(
            Label.record_id.asc(),
            Label.created_at.desc(),
            Label.id.desc(),
        )
        .all()
    )

    latest: dict[int, str] = {}

    for record_id, label, _created_at, _label_id in rows:
        if record_id not in latest:
            latest[record_id] = str(label or "").strip().lower()

    return latest


def _validate_metrics(meta: dict) -> None:
    """Valida estrutura no valor métrika ne'ebé pipeline retorna."""

    missing = [key for key in REQUIRED_METRICS if key not in meta]

    if missing:
        raise ValidationError(
            "Hasil training tidak lengkap. Field yang tidak ditemukan: "
            + ", ".join(missing)
        )

    try:
        n_samples = int(meta["n_samples"])
        n_train = int(meta["n_train"])
        n_test = int(meta["n_test"])
        n_classes = int(meta["n_classes"])
        feature_count = int(meta["feature_count"])
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Hasil training memiliki jumlah sampel atau fitur yang tidak valid."
        ) from exc

    if min(n_samples, n_train, n_test, n_classes, feature_count) < 0:
        raise ValidationError(
            "Hasil training tidak boleh memiliki jumlah negatif."
        )

    if n_train + n_test != n_samples:
        raise ValidationError(
            "Jumlah sampel training dan testing tidak sesuai dengan total sampel."
        )

    if n_classes != len(meta["classes"]):
        raise ValidationError(
            "Jumlah kelas tidak sesuai dengan daftar kelas hasil training."
        )

    for metric_name in (
        "accuracy",
        "f1_macro",
        "precision_macro",
        "recall_macro",
    ):
        try:
            value = float(meta[metric_name])
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"Metrik {metric_name} tidak valid."
            ) from exc

        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValidationError(
                f"Metrik {metric_name} harus berada antara 0 dan 1."
            )

    matrix = meta["confusion_matrix"]

    if not isinstance(matrix, list):
        raise ValidationError("Confusion matrix tidak valid.")

    if len(matrix) != n_classes:
        raise ValidationError(
            "Ukuran confusion matrix tidak sesuai dengan jumlah kelas."
        )

    for row in matrix:
        if not isinstance(row, list) or len(row) != n_classes:
            raise ValidationError(
                "Struktur confusion matrix tidak valid."
            )

        for value in row:
            if not isinstance(value, int) or value < 0:
                raise ValidationError(
                    "Confusion matrix harus berisi bilangan bulat non-negatif."
                )


def train_model(db: Session, **kwargs) -> dict:
    """
    Treina modelu sentiment analysis no rai métrika
    ne'ebé mai husi ml_pipeline.train().
    """

    latest = _latest_label_map(db)

    if not latest:
        raise ValidationError(
            "Belum ada record berlabel. Lakukan labeling terlebih dahulu."
        )

    records = (
        db.query(TextRecord)
        .filter(TextRecord.id.in_(list(latest.keys())))
        .order_by(TextRecord.id.asc())
        .all()
    )

    texts: list[str] = []
    labels: list[str] = []

    for record in records:
        label = latest.get(record.id, "")

        if not label:
            continue

        if label not in VALID_LABELS:
            raise ValidationError(
                f"Label '{label}' pada record ID {record.id} tidak valid. "
                "Gunakan negative, neutral, atau positive."
            )

        text = (record.text_clean or record.text or "").strip()

        if not text:
            continue

        texts.append(text)
        labels.append(label)

    total_samples = len(texts)

    if total_samples < settings.MIN_SAMPLES_TO_TRAIN:
        raise ValidationError(
            f"Minimal {settings.MIN_SAMPLES_TO_TRAIN} sampel berlabel "
            "dan memiliki teks valid diperlukan. "
            f"Saat ini tersedia {total_samples} sampel."
        )

    class_counts = Counter(labels)

    if len(class_counts) < 2:
        raise ValidationError(
            "Training membutuhkan minimal dua kelas sentimen yang berbeda. "
            f"Kelas tersedia: {dict(class_counts)}."
        )

    # Stratified split presiza amostra rua ka liu ba kada klase.
    insufficient = {
        label: count
        for label, count in class_counts.items()
        if count < 2
    }

    if insufficient:
        details = ", ".join(
            f"{label}: {count} sampel"
            for label, count in sorted(insufficient.items())
        )

        raise ValidationError(
            "Training dibatalkan karena jumlah sampel per kelas belum cukup "
            "untuk evaluasi stratified. "
            f"Kelas yang kurang: {details}. "
            "Tambahkan label yang benar melalui halaman Labeling, "
            "kemudian jalankan training kembali."
        )

    # Pipeline mak valida test_size no halo stratified split.
    meta = ml_pipeline.train(texts, labels, **kwargs)

    if not isinstance(meta, dict):
        raise ValidationError(
            "Hasil training tidak valid: pipeline tidak mengembalikan objek metrik."
        )

    _validate_metrics(meta)

    # Kria versao foun ho timestamp microsecond atu hamenus kolizaun.
    version = (
        "v"
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    )

    mv = ModelVersion(
        version=version,
        algorithm="DecisionTree",
        vectorizer="TfidfVectorizer",
        artifact_path=(
            f"{settings.ARTIFACT_DIR}/{settings.MODEL_FILENAME}"
        ),
        meta_path=(
            f"{settings.ARTIFACT_DIR}/{settings.META_FILENAME}"
        ),
        n_samples=int(meta["n_samples"]),
        n_train=int(meta["n_train"]),
        n_test=int(meta["n_test"]),
        n_classes=int(meta["n_classes"]),
        feature_count=int(meta["feature_count"]),
        accuracy=float(meta["accuracy"]),
        f1_macro=float(meta["f1_macro"]),
        precision_macro=float(meta["precision_macro"]),
        recall_macro=float(meta["recall_macro"]),
        confusion_matrix_json=json.dumps(meta["confusion_matrix"]),
        classes_json=json.dumps(meta["classes"]),
        is_active=True,
    )

    try:
        # Modelu anteriór sai inativu.
        (
            db.query(ModelVersion)
            .filter(ModelVersion.is_active.is_(True))
            .update(
                {ModelVersion.is_active: False},
                synchronize_session=False,
            )
        )

        db.add(mv)
        db.commit()
        db.refresh(mv)

    except Exception:
        db.rollback()
        raise

    return {
        "trained": True,
        "version": version,
        **meta,
    }


def training_status() -> dict:
    """Fila status atual husi modelu."""

    ready = ml_pipeline.is_ready()

    return {
        "ready": ready,
        "meta": ml_pipeline.meta if ready else {},
    }