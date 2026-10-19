from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/")
def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}