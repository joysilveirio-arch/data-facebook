from backend.app.database.connection import Base, engine
from backend.app.core.logging import logger


def init_db() -> None:
    from backend.app.models import (
        dataset,
        text_record,
        label,
        preprocessing_job,
        model_version,
        prediction_history,
        audit_log,
        user,
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", engine.url)