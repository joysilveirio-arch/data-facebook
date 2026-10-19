from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_list_records_empty_or_ok():
    r = client.get("/api/v1/datasets/?page=1&page_size=5")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data

def test_import_missing_file():
    r = client.post("/api/v1/datasets/import", json={"file_path": "tidak_ada.csv", "format": "csv"})
    assert r.status_code == 404

def test_label_invalid_class():
    r = client.post("/api/v1/labels/999999", json={"label": "invalid"})
    assert r.status_code in (400, 404)