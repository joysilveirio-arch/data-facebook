import hmac
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.user import User

router = APIRouter()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:
    """Kripta password ho salt aleatoriu."""
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000,
    ).hex()

    return f"{salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifika password ho hash ne'ebe rai iha database."""
    try:
        salt, saved_hash = stored_hash.split("$", 1)

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            310000,
        ).hex()

        return hmac.compare_digest(candidate, saved_hash)

    except (ValueError, AttributeError):
        return False


# =========================================================
# REQUEST SCHEMAS
# =========================================================

class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)


# =========================================================
# REGISTER
# POST /api/v1/auth/register
# =========================================================

@router.post("/register")
def register(
    data: RegisterInput,
    db: Session = Depends(get_db),
):
    username = data.username.strip()
    email = data.email.strip().lower()

    if not username:
        raise HTTPException(
            status_code=422,
            detail="Username labele la bele mamuk.",
        )

    if not email:
        raise HTTPException(
            status_code=422,
            detail="Email labele mamuk.",
        )

    existing_user = db.query(User).filter(
        (User.username == username)
        | (User.email == email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username ka email ne'e uza ona.",
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="La konsege kria konta. Favor koko fali.",
        )

    return {
        "message": "Konta kria ho susesu.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    }


# =========================================================
# LOGIN
# POST /api/v1/auth/login
# =========================================================

@router.post("/login")
def login(
    data: LoginInput,
    request: Request,
    db: Session = Depends(get_db),
):
    identity = data.username.strip()

    user = db.query(User).filter(
        (User.username == identity)
        | (User.email == identity.lower())
    ).first()

    if (
        not user
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Username/email ka password sala.",
        )

    # Hamo session tuan no kria session foun.
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    return {
        "message": "Login ho susesu.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    }


# =========================================================
# CURRENT USER
# GET /api/v1/auth/me
# =========================================================

@router.get("/me")
def current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Favor login uluk.",
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active.is_(True),
    ).first()

    if not user:
        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail="Sessão la válidu. Favor login fali.",
        )

    return {
        "authenticated": True,
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


# =========================================================
# LOGOUT
# POST /api/v1/auth/logout
# =========================================================

@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Logout ho susesu.",
    }