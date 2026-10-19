
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import NotFoundError, ImportError_
from backend.app.models.dataset import Dataset
from backend.app.models.text_record import TextRecord


# ============================================================
# PATH RESOLUTION
# ============================================================

def _resolve(file_path: str) -> Path:
    """Resolve absolute paths or paths relative to DATASET_DIR."""

    if not file_path or not str(file_path).strip():
        raise ValueError("File path la bele mamuk.")

    path = Path(file_path).expanduser()

    if not path.is_absolute():
        path = Path(settings.DATASET_DIR) / path

    path = path.resolve()

    if not path.exists() or not path.is_file():
        raise NotFoundError(f"File la hetan: {path}")

    if path.suffix.lower() not in {".csv", ".json"}:
        raise ValueError("Formatu file tenke CSV ka JSON.")

    return path


# ============================================================
# VALUE HELPERS
# ============================================================

def _get(
    data: Dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    """Get values from flat columns or nested JSON objects."""

    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]

        value: Any = data

        for part in key.replace("/", ".").split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]

        if value not in (None, ""):
            return value

    return default


def _clean(value: Any) -> str:
    """Normalize whitespace and convert values to strings."""

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)

    return re.sub(r"\s+", " ", str(value)).strip()


def _optional_string(value: Any) -> Optional[str]:
    result = _clean(value)
    return result or None


def _to_int(value: Any) -> int:
    """Convert values such as '12', '12.0' or '1,200' to integers."""

    if value is None or isinstance(value, bool):
        return 0

    if isinstance(value, str):
        value = value.strip().replace(",", "")

    if value == "":
        return 0

    try:
        return int(float(value))
    except (ValueError, TypeError, OverflowError):
        return 0


# ============================================================
# ROW MAPPING
# ============================================================

def _map_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map Facebook CSV/JSON fields to TextRecord columns."""

    comment_id = _get(
        row,
        "commentId",
        "comment_id",
        "comment.id",
        "id",
    )

    text = _get(
        row,
        "text",
        "message",
        "comment",
        default="",
    )

    author_name = _get(
        row,
        "author/name",
        "author.name",
        "authorName",
        "author_name",
    )

    author_id = _get(
        row,
        "author/id",
        "author.id",
        "authorId",
        "author_id",
    )

    post_title = _get(row, "postTitle", "post_title")

    date = _get(
        row,
        "date",
        "created_time",
        "createdAt",
        "created_at",
        "timestamp",
    )

    likes = _get(
        row,
        "likesCount",
        "likes_count",
        "likes",
        default=0,
    )

    source_url = _get(
        row,
        "facebookUrl",
        "facebook_url",
        "commentUrl",
        "comment_url",
        "source_url",
        "url",
    )

    return {
        "comment_id": _optional_string(comment_id),
        "text": _clean(text),
        "text_clean": None,
        "author_name": _optional_string(author_name),
        "author_id": _optional_string(author_id),
        "post_title": _optional_string(post_title),
        "date": _optional_string(date),
        "likes_count": max(0, _to_int(likes)),
        "source_url": _optional_string(source_url),
    }


# ============================================================
# CSV READER
# ============================================================

def _read_csv(path: Path) -> List[Dict[str, Any]]:
    """Read CSV using common encodings and delimiter detection."""

    last_error: Optional[Exception] = None

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with path.open(
                "r",
                encoding=encoding,
                newline="",
            ) as file:
                sample = file.read(65536)
                file.seek(0)

                if not sample.strip():
                    return []

                try:
                    dialect = csv.Sniffer().sniff(
                        sample,
                        delimiters=",;\t|",
                    )
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(file, dialect=dialect)

                if not reader.fieldnames:
                    raise ValueError("CSV la iha header.")

                reader.fieldnames = [
                    (name or "").strip().lstrip("\ufeff")
                    for name in reader.fieldnames
                ]

                rows: List[Dict[str, Any]] = []

                for row in reader:
                    if not row:
                        continue

                    # Skip empty rows and ignore extra columns.
                    row.pop(None, None)

                    if not any(
                        value is not None and str(value).strip()
                        for value in row.values()
                    ):
                        continue

                    rows.append(row)

                return rows

        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(
        f"La konsege lee CSV. Encoding error: {last_error}"
    )


# ============================================================
# JSON READER
# ============================================================

def _read_json(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON list or a common exported JSON wrapper."""

    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        rows = payload

    elif isinstance(payload, dict):
        rows = None

        for key in ("data", "items", "results", "posts", "comments"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break

        if rows is None:
            for value in payload.values():
                if isinstance(value, list):
                    rows = value
                    break

        if rows is None:
            raise ValueError(
                "JSON la valid: la hetan lista objetu."
            )

    else:
        raise ValueError("JSON tenke lista ka objetu.")

    return [item for item in rows if isinstance(item, dict)]


# ============================================================
# READ SOURCE ROWS
# ============================================================

def _iter_rows(
    path: Path,
    fmt: Optional[str] = None,
) -> List[Dict[str, Any]]:
    file_format = (fmt or path.suffix.lstrip(".")).lower().strip()

    if file_format == "csv":
        return _read_csv(path)

    if file_format == "json":
        return _read_json(path)

    raise ValueError(f"Formatu la suporta: {file_format}")


# ============================================================
# IMPORT DATASET
# ============================================================

def import_dataset(
    file_path: str,
    fmt: Optional[str],
    db: Session,
    *,
    reset: bool = False,
    dataset_name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Import Facebook text records.

    comment_id must be unique across the TextRecord table.
    Existing IDs are skipped unless reset=True clears old datasets.
    """

    try:
        path = _resolve(file_path)
        file_format = (fmt or path.suffix.lstrip(".")).lower().strip()

        if file_format not in {"csv", "json"}:
            raise ValueError("Formatu tenke CSV ka JSON.")

        rows = _iter_rows(path, file_format)
        name = _clean(dataset_name) or path.stem

        if not name:
            raise ValueError("Dataset name la bele mamuk.")

        if reset:
            # Delete ORM objects so configured cascades can run.
            old_datasets = db.query(Dataset).all()

            for old_dataset in old_datasets:
                db.delete(old_dataset)

            db.flush()
            dataset = None
        else:
            dataset = (
                db.query(Dataset)
                .filter(Dataset.name == name)
                .first()
            )

        if dataset is None:
            dataset = Dataset(
                name=name,
                source_file=str(path),
                format=file_format,
                description=description,
                total_records=0,
                is_active=True,
            )
            db.add(dataset)
            db.flush()
        else:
            dataset.source_file = str(path)
            dataset.format = file_format

            if description is not None:
                dataset.description = description

        # comment_id is globally unique in the database.
        existing_ids = {
            str(comment_id)
            for (comment_id,) in db.query(TextRecord.comment_id).all()
            if comment_id is not None
        }

        imported = 0
        skipped = 0
        missing_id = 0
        missing_text = 0
        duplicate_rows = 0

        for row in rows:
            data = _map_row(row)

            if not data["comment_id"]:
                skipped += 1
                missing_id += 1
                continue

            if not data["text"]:
                skipped += 1
                missing_text += 1
                continue

            comment_id = data["comment_id"]

            if comment_id in existing_ids:
                skipped += 1
                duplicate_rows += 1
                continue

            record = TextRecord(
                dataset_id=dataset.id,
                **data,
            )

            db.add(record)
            existing_ids.add(comment_id)
            imported += 1

        db.flush()

        dataset.total_records = (
            db.query(TextRecord)
            .filter(TextRecord.dataset_id == dataset.id)
            .count()
        )

        dataset_id_result = dataset.id
        dataset_name_result = dataset.name
        dataset_total = dataset.total_records

        db.commit()

        total_now = db.query(TextRecord).count()

        return {
            "success": True,
            "message": "Import dataset susesu.",
            "dataset_id": dataset_id_result,
            "dataset_name": dataset_name_result,
            "source_file": str(path),
            "format": file_format,
            "source_rows": len(rows),
            "imported": imported,
            "skipped": skipped,
            "missing_id": missing_id,
            "missing_text": missing_text,
            "duplicate_rows": duplicate_rows,
            "dataset_total_records": dataset_total,
            "total_now": total_now,
            "reset": reset,
        }

    except Exception as exc:
        db.rollback()

        if isinstance(exc, (NotFoundError, ImportError_)):
            raise

        raise ImportError_(
            f"Import dataset falla: {exc}"
        ) from exc


# ============================================================
# LIST DATASETS
# ============================================================

def list_datasets(db: Session) -> List[Dataset]:
    return (
        db.query(Dataset)
        .order_by(Dataset.id.desc())
        .all()
    )


# ============================================================
# GET DATASET BY ID
# ============================================================

def get_dataset(
    db: Session,
    dataset_id: int,
) -> Dataset:
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )

    if dataset is None:
        raise NotFoundError(
            f"Dataset ho ID {dataset_id} la hetan."
        )

    return dataset
