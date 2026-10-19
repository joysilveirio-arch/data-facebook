from fastapi import APIRouter

from backend.app.api.v1 import (
    health,
    datasets,
    records,
    preprocessing,
    labeling,
    training,
    prediction,
    analytics,
)

# ============================================================
# API V1 ROUTER
# Main prefix: /api/v1
# ============================================================

api_router = APIRouter()


# ============================================================
# HEALTH
# URL: /api/v1/health
# ============================================================

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)


# ============================================================
# DATASET IMPORT AND MANAGEMENT
# URL: /api/v1/datasets
# ============================================================

api_router.include_router(
    datasets.router,
    prefix="/datasets",
    tags=["datasets"],
)


# ============================================================
# RECORDS CRUD
# URL: /api/v1/records
# ============================================================

api_router.include_router(
    records.router,
    prefix="/records",
    tags=["records"],
)


# ============================================================
# DATA PREPROCESSING
# URL: /api/v1/preprocessing
# ============================================================

api_router.include_router(
    preprocessing.router,
    prefix="/preprocessing",
    tags=["preprocessing"],
)


# ============================================================
# MANUAL SENTIMENT LABELS
# URL: /api/v1/labels
# ============================================================

api_router.include_router(
    labeling.router,
    prefix="/labels",
    tags=["labels"],
)


# ============================================================
# MACHINE LEARNING TRAINING
# URL: /api/v1/training
# ============================================================

api_router.include_router(
    training.router,
    prefix="/training",
    tags=["training"],
)


# ============================================================
# SENTIMENT PREDICTION
# URL: /api/v1/predict
# ============================================================

api_router.include_router(
    prediction.router,
    prefix="/predict",
    tags=["prediction"],
)


# ============================================================
# ANALYTICS AND VISUALIZATION
# URL: /api/v1/analytics
# ============================================================

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
)