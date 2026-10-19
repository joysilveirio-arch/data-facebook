import os
from pathlib import Path

from fastapi import (
    FastAPI,
    Request,
    Depends,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.init_db import init_db
from backend.app.api.v1.router import api_router
from backend.app.api.v1 import auth


# ============================================================
# PROJECT PATHS
# main.py: project/backend/app/main.py
# Frontend: project/frontend/
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Analisis sentimen komentar Facebook multibahasa "
        "(Tetum/ID/PT/EN)."
    ),
)


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET:
    SESSION_SECRET = "LOCAL-ONLY-CHANGE-THIS-SESSION-SECRET"

    logger.warning(
        "SESSION_SECRET la configura. Uza secret lokal deit."
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=(
        os.getenv("COOKIE_HTTPS_ONLY", "false").lower() == "true"
    ),
    max_age=60 * 60 * 8,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FRONTEND CACHE CONTROL
# ============================================================

@app.middleware("http")
async def frontend_no_cache(request: Request, call_next):
    response = await call_next(request)

    path = request.url.path.lower()

    is_frontend_request = (
        path == "/"
        or path.endswith(
            (
                ".html",
                ".css",
                ".js",
                ".ico",
                ".json",
                ".svg",
                ".woff",
                ".woff2",
            )
        )
        or path.startswith("/pages/")
        or path.startswith("/assets/")
    )

    if is_frontend_request:
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": str(exc.detail),
            "path": str(request.url),
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exc_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exc_handler(
    request: Request,
    exc: Exception,
):
    logger.exception("Unhandled error: %s", exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
        },
    )


# ============================================================
# DATABASE STARTUP
# ============================================================

@app.on_event("startup")
async def on_startup():
    init_db()
    logger.info("Application started.")


# ============================================================
# HEALTH CHECK
# PUBLIC: NO LOGIN REQUIRED
# ============================================================

@app.get("/api/health", tags=["health"])
def root_health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ============================================================
# AUTHENTICATION ROUTES
# PUBLIC: REGISTER AND LOGIN
# ============================================================

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"],
)


# ============================================================
# LOGIN PROTECTION
# ============================================================

def require_login(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Favor login uluk atu asesu sistema.",
        )


# ============================================================
# MAIN API ROUTER
# API ROUTES REQUIRE LOGIN
# ============================================================

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
    dependencies=[Depends(require_login)],
)


# ============================================================
# FRONTEND STATIC FILES
# MOUNT AFTER API ROUTES
# ============================================================

if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(
            directory=str(FRONTEND_DIR),
            html=True,
            check_dir=True,
        ),
        name="frontend",
    )

    logger.info(
        "Frontend directory found: %s",
        FRONTEND_DIR,
    )
    logger.info(
        "Dashboard URL: http://127.0.0.1:8000/"
    )
    logger.info(
        "Login URL: http://127.0.0.1:8000/login.html"
    )

else:
    logger.error(
        "Frontend directory not found: %s",
        FRONTEND_DIR,
    )