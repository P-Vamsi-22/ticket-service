"""Password hashing (Argon2id) and JWT create/verify."""
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app import config

password_hash = PasswordHash.recommended()  # Argon2id

# Checked when the email is unknown, so a wrong email takes as long as a wrong password.
DUMMY_HASH = password_hash.hash("not-a-real-password")


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "role": role,  # informational for the UI; the server always re-reads the role from the DB
        "iat": now,
        "exp": now + timedelta(minutes=config.ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(claims, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Algorithm is fixed: "none" or any other alg is rejected.
    return jwt.decode(
        token,
        config.JWT_SECRET,
        algorithms=[config.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "iat"]},
    )
