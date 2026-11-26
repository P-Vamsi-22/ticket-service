import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import Token, UserOut
from app.security import DUMMY_HASH, create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# email -> times of recent failed logins (in-memory: fine for one dev server process)
_failed_logins: dict[str, list[float]] = {}


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow. The form field is called "username"; we put the email in it."""
    email = form.username.strip().lower()
    now = time.monotonic()
    recent = [t for t in _failed_logins.get(email, []) if now - t < config.LOCKOUT_SECONDS]
    if len(recent) >= config.MAX_FAILED_LOGINS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed logins. Try again in a few minutes.",
        )

    user = db.scalar(select(User).where(User.email == email))
    stored = user.password_hash if user and user.password_hash else DUMMY_HASH
    ok = verify_password(form.password, stored)
    if user is None or user.password_hash is None or not ok:
        _failed_logins[email] = recent + [now]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _failed_logins.pop(email, None)
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
