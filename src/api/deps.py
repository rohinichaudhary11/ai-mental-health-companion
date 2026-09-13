"""
Shared dependencies for authentication and authorisation.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.db import get_db
from src.api.schemas import UserInDB, UserPublic

logger = logging.getLogger("mental_health_api")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_TO_A_SECURE_RANDOM_VALUE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def check_secret_key() -> None:
    """Warn if the default JWT secret is in use (called once at startup)."""
    if SECRET_KEY == "CHANGE_ME_TO_A_SECURE_RANDOM_VALUE":
        logger.warning(
            "⚠️  JWT_SECRET_KEY is using the default value! "
            "Set a strong, unique secret via the JWT_SECRET_KEY environment variable."
        )


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    data: Dict[str, object],
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

async def get_user_by_email(email: str) -> Optional[UserInDB]:
    try:
        db = get_db()
        doc = await db["users"].find_one({"email": email})
    except Exception as e:
        logger.error("Database error in get_user_by_email: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error: Unable to reach MongoDB.",
        )
    if not doc:
        return None
    doc["id"] = str(doc.get("_id"))
    return UserInDB(**doc)


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    """Decode JWT and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_in_db = await get_user_by_email(email)
    if user_in_db is None or user_in_db.id is None:
        raise credentials_exception

    return UserPublic(
        id=user_in_db.id,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        created_at=user_in_db.created_at,
    )
