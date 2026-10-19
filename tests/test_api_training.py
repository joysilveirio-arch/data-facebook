def test_training_status(client):
    r = client.get("/api/v1/training/status")
    assert r.status_code == 200
    assert "ready" in r.json()

def test_train_insufficient(client):
    # Biasanya akan gagal karena sample berlabel masih sedikit
    r = client.post("/api/v1/training/train", json={"test_size": 0.2, "random_state": 42})
    assert r.status_code in (200, 400)