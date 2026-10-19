import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.training import (
    TrainRequest,
    TrainResult,
    TrainingStatus,
)
from backend.app.services import training_service, audit_service


logger = logging.getLogger("facebook_text_system")

router = APIRouter()


@router.post("/train", response_model=TrainResult)
def train(
    req: TrainRequest,
    db: Session = Depends(get_db),
):
    """
    Treina modelu sentimentu no fila rezultadu avaliasaun.

    HTTP 400:
        Dadus ka konfigurasaun training la válidu.

    HTTP 500:
        Erro inesperadu iha backend.
    """

    try:
        # 1. Treina modelu ho dadus berlabel husi database.
        result = training_service.train_model(
            db,
            test_size=req.test_size,
            max_depth=req.max_depth,
            min_samples_split=req.min_samples_split,
            random_state=req.random_state,
        )

        # 2. Verifika rezultadu molok kria audit log.
        if not isinstance(result, dict):
            raise RuntimeError(
                "Training service returned an invalid result."
            )

        if "version" not in result or "accuracy" not in result:
            raise RuntimeError(
                "Training result is missing required fields."
            )

        # 3. Rai audit log bainhira training susesu.
        try:
            audit_service.log(
                db,
                "train",
                entity="model",
                detail=(
                    f"version={result['version']} "
                    f"acc={float(result['accuracy']):.3f}"
                ),
            )
        except Exception:
            # Audit failure labele subar rezultadu training.
            logger.exception(
                "Training succeeded, but audit logging failed."
            )

        return result

    except ValueError as exc:
        # Dadus seidauk sufisiente, label la válidu,
        # ka parameter training la loos.
        logger.warning(
            "Training validation failed: %s",
            str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        # Rai HTTPException ne'ebé iha ona.
        raise

    except Exception as exc:
        # Rai traceback kompletu iha terminal ba debugging.
        logger.exception(
            "Unexpected error during model training."
        )

        # La hatudu detalhe interno ba utilizadór.
        raise HTTPException(
            status_code=500,
            detail=(
                "Training gagal karena terjadi kesalahan "
                "internal. Periksa log backend untuk detail."
            ),
        ) from exc


@router.get("/status", response_model=TrainingStatus)
def status():
    """
    Retorna status no metadata training modelu.
    """

    try:
        return training_service.training_status()

    except Exception as exc:
        logger.exception(
            "Failed to retrieve training status."
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal mengambil status training model.",
        ) from exc
