"""
Retrain model dari label terbaru.
Usage: python scripts/retrain_model.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.connection import SessionLocal
from backend.app.database.init_db import init_db
from backend.app.services.training_service import train_model


def main():
    init_db()
    db = SessionLocal()
    try:
        result = train_model(db, test_size=0.2, max_depth=None, min_samples_split=2, random_state=42)
        print(f"[OK] Trained version={result['version']} acc={result['accuracy']:.3f} f1={result['f1_macro']:.3f}")
    finally:
        db.close()

if __name__ == "__main__":
    main()