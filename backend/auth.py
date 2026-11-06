import hashlib
import hmac
import secrets

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy import select, insert

from database import get_database, users, sessions


_bearer = HTTPBearer(auto_error=False)

_PASSWORD_SALT_BYTES = 16
_PASSWORD_HASH_BYTES = 64
_SESSION_DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_PASSWORD_SALT_BYTES)

    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=_PASSWORD_HASH_BYTES,
    )

    return f"scrypt${salt.hex()}${password_hash.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, salt_hex, expected_hex = encoded_hash.split("$")

        if algorithm != "scrypt":
            return False

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=2**14,
            r=8,
            p=1,
            dklen=_PASSWORD_HASH_BYTES,
        )

        return hmac.compare_digest(actual.hex(), expected_hex)

    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(database, user_id: int) -> str:

    token = secrets.token_urlsafe(32)

    database.execute(
        insert(sessions).values(
            token_hash=_token_hash(token),
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=_SESSION_DAYS),
        )
    )

    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    database=Depends(get_database),
) -> dict:

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
        )

    session = database.execute(
        select(sessions).where(
            sessions.c.token_hash == _token_hash(credentials.credentials),
            sessions.c.expires_at > datetime.utcnow(),
        )
    ).mappings().first()

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired. Please log in again.",
        )

    user = database.execute(
        select(users).where(users.c.id == session["user_id"])
    ).mappings().first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Your account is unavailable. Please log in again.",
        )

    return dict(user)