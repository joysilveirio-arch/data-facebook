"""
Seed database dengan dataset default (data_facebook.csv).
Usage: python scripts/seed_database.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.connection import SessionLocal
from backend.app.database.init_db import init_db
from backend.app.services.dataset_service import import_dataset


def main():
    init_db()
    db = SessionLocal()
    try:
        result = import_dataset("data_facebook.csv", "csv", db, reset=True, dataset_name="facebook_default")
        print(f"[OK] Imported={result['imported']} Skipped={result['skipped']} Total={result['total_now']}")
    finally:
        db.close()

if __name__ == "__main__":
    main()