from backend.app.database.connection import Base, engine
from backend.app.core.logging import logger

def init_db() -> None:
    # Import semua model agar ter-register ke metadata
    from backend.app.models import (  # noqa
        dataset, text_record, label, preprocessing_job,
        model_version, prediction_history, audit_log,
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", engine.url)