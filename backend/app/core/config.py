from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent                              # facebook_text_system/

class Settings(BaseSettings):
    APP_NAME: str = "Facebook Text Sentiment System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DB_PATH: str = str(BASE_DIR / "data" / "app.db")

    # Dataset
    DATASET_DIR: str = str(BASE_DIR / "data")
    DEFAULT_DATASET: str = "data_facebook.csv"

    # Artifacts (model)
    ARTIFACT_DIR: str = str(BASE_DIR / "artifacts")
    MODEL_FILENAME: str = "dt_tfidf.pkl"
    META_FILENAME: str = "dt_tfidf.meta.json"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # ML
    TFIDF_MAX_FEATURES: int = 5000
    TFIDF_NGRAM_MIN: int = 1
    TFIDF_NGRAM_MAX: int = 2
    TEST_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    MIN_SAMPLES_TO_TRAIN: int = 10

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Pastikan folder ada
Path(settings.ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.DATASET_DIR).mkdir(parents=True, exist_ok=True)