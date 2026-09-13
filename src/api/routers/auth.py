"""
Authentication routes: signup, login, and user profile retrieval.
"""

import logging
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from src.db import get_db
from src.api.schemas import Token, UserCreate, UserPublic
from src.api.deps import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    """
    Create a new user with a hashed password.
    """
    try:
        db = get_db()
        existing = await db["users"].find_one({"email": user.email})
    except Exception as e:
        logger.error("Database error in signup: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error: Unable to reach MongoDB.",
        )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    now = datetime.now(timezone.utc)
    user_doc: Dict[str, object] = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hash_password(user.password),
        "created_at": now,
    }
    try:
        result = await db["users"].insert_one(user_doc)
    except Exception as e:
        logger.error("Database error saving user: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error: Unable to save user to MongoDB.",
        )

    return UserPublic(
        id=str(result.inserted_id),
        email=user.email,
        full_name=user.full_name,
        created_at=now,
    )


@router.post("/login", response_model=Token)
async def login(user: UserCreate):
    """
    Authenticate user and return a JWT access token.
    """
    auth_user = await authenticate_user(user.email, user.password)
    if not auth_user or auth_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": auth_user.email})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    """
    return current_user
