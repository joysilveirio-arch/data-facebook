
import csv
import math
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.core.config import settings
from backend.app.schemas.analytics import OverviewOut
from backend.app.services import analytics_service


router = APIRouter()


# ============================================================
# 1. ANALYTICS BAZEIA BA DATABASE
# ============================================================

@router.get("/overview", response_model=OverviewOut)
def overview(db: Session = Depends(get_db)):
    """
    Retorna analytics bazeia ba dadus iha database.
    Dadus sira kalkula husi analytics_service.
    """
    return analytics_service.overview(db)


# ============================================================
# 2. BUKA CSV ORIJINAL
# ============================================================

def _find_csv() -> Path:
    """
    Buka dataset_facebook.csv iha pasta data/.
    Fatin ne'ebé buka:
      1. settings.PROJECT_ROOT/data/dataset_facebook.csv
      2. Project root/data/dataset_facebook.csv
    """
    candidates = []

    project_root = getattr(settings, "PROJECT_ROOT", None)

    if project_root:
        candidates.append(
            Path(project_root).expanduser()
            / "data"
            / "dataset_facebook.csv"
        )

    # analytics.py -> v1 -> api -> app -> backend -> project root
    project_dir = Path(__file__).resolve().parents[4]

    candidates.append(
        project_dir / "data" / "dataset_facebook.csv"
    )

    # Hamoos path repetidu, maibé mantein ordem.
    unique_candidates = list(dict.fromkeys(candidates))

    for candidate in unique_candidates:
        if candidate.is_file():
            return candidate

    checked_paths = ", ".join(
        str(path) for path in unique_candidates
    )

    raise HTTPException(
        status_code=404,
        detail=(
            "La hetan dataset_facebook.csv. "
            f"Fatin ne'ebé verifica: {checked_paths}"
        ),
    )


# ============================================================
# 3. NORMALIZA NARAN KOLUNA NO VALOR
# ============================================================

def _normalize_column_name(value: Any) -> str:
    """Hamoos naran koluna CSV."""
    return (
        str(value or "")
        .strip()
        .strip('"')
        .lstrip("\ufeff")
        .strip()
    )


def _normalize_row(row: dict) -> dict:
    """Normaliza naran koluna no espasu iha linha ida."""
    normalized = {}

    for key, value in row.items():
        # DictReader bele uza None ba valor extra
        # bainhira linha iha koluna barak liu header.
        if key is None:
            continue

        column = _normalize_column_name(key)

        if isinstance(value, str):
            value = value.strip()

        normalized[column] = value

    return normalized


def _number(value: Any):
    """
    Konverte valor ba float.
    Retorna None se valor mamuk ka la'ós númeru válidu.
    """
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.casefold() in {
        "null",
        "none",
        "nan",
        "na",
        "n/a",
        "unknown",
        "-",
    }:
        return None

    # Suporta númeru hanesan 1,234.
    text = text.replace(",", "")

    try:
        number = float(text)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _choose_column(keys: set, *candidates: str):
    """
    Buka koluna tuir naran alternativa.
    Kompara naran koluna la haree maiúscula/minúscula.
    """
    key_lookup = {
        str(key).strip().casefold(): key
        for key in keys
    }

    for candidate in candidates:
        found = key_lookup.get(candidate.strip().casefold())

        if found is not None:
            return found

    return None


def _date_only(value: Any):
    """
    Extrai data iha formatu YYYY-MM-DD.
    Suporta timestamp ISO ne'ebé komesa ho data.
    """
    if value is None:
        return None

    text = str(value).strip()

    if len(text) < 10:
        return None

    day = text[:10]

    try:
        date.fromisoformat(day)
    except ValueError:
        return None

    return day


def _empty_csv_response(
    filename: str,
    message: str,
) -> dict[str, Any]:
    """Resposta JSON bainhira CSV mamuk ka la iha dadus."""
    return {
        "source": filename,
        "total_records": 0,
        "total_likes": 0,
        "total_comments": 0,
        "avg_likes": 0,
        "missing_cells": 0,
        "date_activity": [],
        "top_authors": [],
        "engagement": [
            {"metric": "Likes", "value": 0},
            {"metric": "Comments", "value": 0},
        ],
        "available_columns": {
            "likes": False,
            "comments": False,
            "author": False,
            "date": False,
        },
        "valid_likes_count": 0,
        "valid_comments_count": 0,
        "message": message,
    }


# ============================================================
# 4. ANALYTICS HUSI CSV ORIJINAL
# ============================================================

@router.get("/source-csv", response_model=dict[str, Any])
def source_csv_visualization() -> dict[str, Any]:
    """
    Lee dataset CSV orijinál no prepara sumáriu ba gráfiku.

    Endpoint ida-ne'e:
      - La altera CSV orijinál.
      - La altera database.
      - Retorna JSON ba frontend.
    """
    csv_path = _find_csv()

    # --------------------------------------------------------
    # Lee CSV no deteta delimitador
    # --------------------------------------------------------

    try:
        with csv_path.open(
            mode="r",
            encoding="utf-8-sig",
            errors="replace",
            newline="",
        ) as file:
            sample = file.read(16384)
            file.seek(0)

            try:
                dialect = csv.Sniffer().sniff(
                    sample,
                    delimiters=",;\t|",
                )
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(
                file,
                dialect=dialect,
            )

            if not reader.fieldnames:
                return _empty_csv_response(
                    csv_path.name,
                    "CSV mamuk ka la iha header.",
                )

            headers = [
                _normalize_column_name(name)
                for name in reader.fieldnames
            ]

            rows = []

            for row in reader:
                if not row:
                    continue

                normalized_row = _normalize_row(row)

                # Ignora linha ne'ebé koluna hotu mamuk.
                if not any(
                    str(value or "").strip()
                    for value in normalized_row.values()
                ):
                    continue

                rows.append(normalized_row)

    except (OSError, csv.Error, UnicodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"La konsege lee CSV: {exc}",
        ) from exc

    if not rows:
        return _empty_csv_response(
            csv_path.name,
            "CSV la iha linha dadus.",
        )

    # --------------------------------------------------------
    # Identifika koluna sira
    # --------------------------------------------------------

    keys = set().union(
        *(row.keys() for row in rows)
    )

    likes_key = _choose_column(
        keys,
        "likesCount",
        "likes_count",
        "likes",
        "Likes",
        "like_count",
        "total_likes",
    )

    comments_key = _choose_column(
        keys,
        "commentsCount",
        "comments_count",
        "comments",
        "Comments",
        "comment_count",
        "total_comments",
    )

    author_key = _choose_column(
        keys,
        "author/name",
        "profileName",
        "author_name",
        "author",
        "Author",
        "page_name",
        "pageName",
        "name",
    )

    date_key = _choose_column(
        keys,
        "date",
        "created_at",
        "createdAt",
        "Date",
        "timestamp",
        "time",
        "published_at",
    )

    # --------------------------------------------------------
    # Valida koluna obrigatória
    # --------------------------------------------------------

    missing_columns = []

    if likes_key is None:
        missing_columns.append("Likes")

    if comments_key is None:
        missing_columns.append("Comments")

    if missing_columns:
        raise HTTPException(
            status_code=422,
            detail=(
                "CSV la iha koluna importante: "
                + ", ".join(missing_columns)
                + ". Favor verifica header CSV."
            ),
        )

    # --------------------------------------------------------
    # Kalkula likes no comments
    # --------------------------------------------------------

    likes_values = [
        _number(row.get(likes_key))
        for row in rows
    ]

    comments_values = [
        _number(row.get(comments_key))
        for row in rows
    ]

    valid_likes = [
        value
        for value in likes_values
        if value is not None
    ]

    valid_comments = [
        value
        for value in comments_values
        if value is not None
    ]

    total_likes = sum(valid_likes)
    total_comments = sum(valid_comments)

    # Média likes bazeia ba valor válidu de'it.
    avg_likes = (
        total_likes / len(valid_likes)
        if valid_likes
        else 0
    )

    # --------------------------------------------------------
    # Konta missing cells
    # --------------------------------------------------------

    missing_cells = 0

    for row in rows:
        for header in headers:
            value = row.get(header)

            if value is None or not str(value).strip():
                missing_cells += 1

    # --------------------------------------------------------
    # Top 10 autores
    # --------------------------------------------------------

    authors = Counter()

    if author_key is not None:
        for row in rows:
            author = " ".join(
                str(row.get(author_key) or "").split()
            )

            if not author:
                author = "Unknown"

            authors[author] += 1

    top_authors = [
        {
            "author": author,
            "count": count,
        }
        for author, count in authors.most_common(10)
    ]

    # --------------------------------------------------------
    # Atividade post tuir loron
    # --------------------------------------------------------

    dates = Counter()

    if date_key is not None:
        for row in rows:
            day = _date_only(row.get(date_key))

            if day:
                dates[day] += 1

    # Foti loron ikus 30 ne'ebé iha atividade.
    latest_dates = sorted(dates.items())[-30:]

    date_activity = [
        {
            "date": day,
            "count": count,
        }
        for day, count in latest_dates
    ]

    # --------------------------------------------------------
    # Resposta JSON ba frontend
    # --------------------------------------------------------

    return {
        "source": csv_path.name,
        "total_records": len(rows),
        "total_likes": int(total_likes),
        "total_comments": int(total_comments),
        "avg_likes": round(avg_likes, 4),
        "missing_cells": missing_cells,
        "date_activity": date_activity,
        "top_authors": top_authors,
        "engagement": [
            {
                "metric": "Likes",
                "value": int(total_likes),
            },
            {
                "metric": "Comments",
                "value": int(total_comments),
            },
        ],
        "available_columns": {
            "likes": likes_key is not None,
            "comments": comments_key is not None,
            "author": author_key is not None,
            "date": date_key is not None,
        },
        "valid_likes_count": len(valid_likes),
        "valid_comments_count": len(valid_comments),
    }
