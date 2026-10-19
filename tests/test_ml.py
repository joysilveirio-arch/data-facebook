import pytest
from backend.services import ml_service

def test_predict_requires_training():
    # Bila model belum dilatih dan tidak ada file, predict harus error
    if not ml_service.is_ready():
        with pytest.raises(RuntimeError):
            ml_service.predict_text("test")

def test_predict_batch_requires_training():
    if not ml_service.is_ready():
        with pytest.raises(RuntimeError):
            ml_service.predict_batch(["a","b"])