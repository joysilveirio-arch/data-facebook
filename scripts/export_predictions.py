"""
Ekspor seluruh prediksi ke CSV.
Usage: python scripts/export_predictions.py
"""
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.connection import SessionLocal
from backend.app.models.text_record import TextRecord
from backend.app.models.prediction_history import PredictionHistory

OUT = Path(__file__).resolve().parent.parent / "backend" / "data" / "predictions_export.csv"

def main():
    db = SessionLocal()
    try:
        rows = db.query(PredictionHistory).order_by(PredictionHistory.id).all()
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "record_id", "predicted_label", "confidence", "created_at"])
            for r in rows:
                w.writerow([r.id, r.record_id, r.predicted_label, r.confidence, r.created_at])
        print(f"[OK] Exported {len(rows)} predictions -> {OUT}")
    finally:
        db.close()

if __name__ == "__main__":
    main()