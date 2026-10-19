def test_label_invalid(client):
    r = client.post("/api/v1/labels/999999", json={"label": "invalid"})
    assert r.status_code in (400, 404, 422)

def test_label_stats(client):
    r = client.get("/api/v1/labels/stats")
    assert r.status_code == 200
    data = r.json()
    assert "positive" in data and "negative" in data and "neutral" in data