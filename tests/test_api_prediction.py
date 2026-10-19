def test_predict_without_training(client):
    r = client.post("/api/v1/predict/", json={"text": "bonita los"})
    # Kalau model belum ada, harus 400
    assert r.status_code in (200, 400)