import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
from backend.app.core.config import settings

MODEL_PATH = Path(settings.ARTIFACT_DIR) / settings.MODEL_FILENAME
META_PATH = Path(settings.ARTIFACT_DIR) / settings.META_FILENAME

def save_pipeline(payload: Dict[str, Any], meta: Dict[str, Any]) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def load_pipeline() -> Optional[Dict[str, Any]]:
    if not MODEL_PATH.exists():
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def load_meta() -> Dict[str, Any]:
    if not META_PATH.exists():
        return {}
    with open(META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def exists() -> bool:
    return MODEL_PATH.exists()