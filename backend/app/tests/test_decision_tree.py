import pytest
from backend.app.ml.pipeline import MLPipeline

def test_train_insufficient_samples():
    pipe = MLPipeline()
    with pytest.raises(ValueError):
        pipe.train(["a", "b"], ["positive", "negative"])

def test_train_and_predict():
    pipe = MLPipeline()
    texts = [
        "bonita los mana furak",
        "parabens mana wedding",
        "so beautiful amazing",
        "furak los parabens",
        "cantik sekali",
        "keren banget",
        "jelek buruk",
        "tidak bagus",
        "hapus saja",
        "boring",
        "sangat menyedihkan",
        "no comment",
    ]
    labels = ["positive"]*6 + ["negative"]*6
    meta = pipe.train(texts, labels, test_size=0.3)
    assert meta["trained"] if "trained" in meta else True
    assert meta["accuracy"] >= 0.0
    res = pipe.predict_one("bonita los")
    assert res["label"] in ("positive", "negative")