"""
FastAPI application entry point for AI Mental Health Companion.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False

from src.db import get_db
from src.db.mongo import close_client
import src.api.state as state
from src.api.deps import check_secret_key
from src.api.schemas import HealthResponse
from src.api.services.demo_classifier import DemoClassifier
from src.api.routers import (
    analytics_router,
    auth_router,
    chat_router,
    journal_router,
    medical_router,
    mood_router,
    predict_router,
)
from src.inference.model_loader import load_classifier

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mental_health_api")

# Rate Limiter
if HAS_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
else:
    limiter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup initialization
    and clean shutdown of resources.
    """
    # 1. Check JWT secret strength
    check_secret_key()

    # 2. Model initialization
    model_path = Path("models")
    if model_path.exists() and (model_path / "config.json").exists():
        try:
            logger.info("Loading fine-tuned model from %s...", model_path)
            state.classifier = load_classifier(str(model_path))
            state.model_loaded = True
            logger.info("Fine-tuned model loaded successfully.")
        except Exception as e:
            logger.warning("Failed to load fine-tuned model: %s. Falling back to DemoClassifier.", e)
            state.classifier = DemoClassifier()
            state.model_loaded = True
    else:
        logger.info("No fine-tuned model found at 'models/'. Using DemoClassifier.")
        state.classifier = DemoClassifier()
        state.model_loaded = True

    # 3. Create MongoDB indexes (best effort only if connected)
    try:
        db = get_db()
        await db.command("ping")
        await db["users"].create_index("email", unique=True)
        await db["mood_logs"].create_index([("user_id", 1), ("created_at", -1)])
        await db["journal_entries"].create_index([("user_id", 1), ("created_at", -1)])
        await db["chat_history"].create_index([("user_id", 1), ("created_at", -1)])
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.info("MongoDB offline or unreachable at startup; index setup skipped.")

    yield

    # Shutdown
    logger.info("Shutting down Mental Health Companion API...")
    await close_client()


# FastAPI App
app = FastAPI(
    title="Mental Health Companion API",
    description="AI-Powered Emotion Classification, Therapeutic Chat, and Wellness Recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate limiter to app state if available
if HAS_SLOWAPI and limiter is not None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
allowed_origins_env = os.getenv("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(predict_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(mood_router)
app.include_router(journal_router)
app.include_router(medical_router)
app.include_router(analytics_router)


# ---------------------------------------------------------------------------
# General & Health Check Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
async def root():
    """Root metadata endpoint."""
    return {
        "message": "Mental Health Companion API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "chat": "/api/chat",
            "health": "/healthcheck",
            "docs": "/docs",
        },
    }


@app.get("/healthcheck", response_model=HealthResponse, tags=["Health"])
async def healthcheck():
    """
    Health check endpoint returning API status, model status, and MongoDB connectivity.
    """
    db_connected = False
    db_status = "disconnected"
    db_error: Optional[str] = None

    try:
        db = get_db()
        await db.command("ping")
        db_connected = True
        db_status = "connected"
    except Exception as e:
        db_error = f"{type(e).__name__}: {str(e)}"
        logger.warning("Healthcheck database ping failed: %s", db_error)

    return HealthResponse(
        status="healthy" if (state.model_loaded and db_connected) else "degraded",
        model_loaded=state.model_loaded,
        database_connected=db_connected,
        database_status=db_status,
        database_error=db_error,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
