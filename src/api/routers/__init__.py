"""
FastAPI router package.
"""

from src.api.routers.auth import router as auth_router
from src.api.routers.predict import router as predict_router
from src.api.routers.mood import router as mood_router
from src.api.routers.journal import router as journal_router
from src.api.routers.chat import router as chat_router
from src.api.routers.medical import router as medical_router
from src.api.routers.analytics import router as analytics_router

__all__ = [
    "auth_router",
    "predict_router",
    "mood_router",
    "journal_router",
    "chat_router",
    "medical_router",
    "analytics_router",
]
