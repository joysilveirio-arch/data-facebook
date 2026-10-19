def test_list_datasets(client):
    r = client.get("/api/v1/datasets/")
    assert r.status_code == 200

def test_import_missing_file(client):
    r = client.post("/api/v1/datasets/import", json={"file_path": "tidak_ada.csv", "format": "csv"})
    assert r.status_code == 404

def test_list_records(client):
    r = client.get("/api/v1/records/?page=1&page_size=5")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data