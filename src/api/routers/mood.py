"""
Mood tracking endpoints.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter

from src.db import get_db
from src.api.schemas import MoodLog

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api", tags=["Mood"])

# In-memory store fallback for demo or when DB is unavailable
MOOD_LOGS: List[MoodLog] = []


@router.post("/mood-log")
async def log_mood(entry: MoodLog):
    """
    Log a mood entry for a user.
    """
    MOOD_LOGS.append(entry)

    # Best-effort persistence to MongoDB
    try:
        db = get_db()
        await db["mood_logs"].insert_one(entry.model_dump())
    except Exception as e:
        logger.warning("MongoDB insert for mood-log skipped/failed: %s", e)

    return {"status": "ok", "logged_at": entry.created_at.isoformat()}


@router.get("/mood-log")
async def get_mood_logs(
    user_id: Optional[str] = None,
    limit: int = 100,
    period: Optional[str] = None,
):
    """
    Return recent mood logs for a user (or all, if user_id is omitted).
    """
    period_lower = (period or "").lower().strip()
    since: Optional[datetime] = None
    if period_lower in {"week", "weekly", "7d", "7days"}:
        since = datetime.now(timezone.utc) - timedelta(days=7)
    elif period_lower in {"month", "monthly", "30d", "30days"}:
        since = datetime.now(timezone.utc) - timedelta(days=30)

    # Try MongoDB first
    try:
        db = get_db()
        query: Dict[str, object] = {}
        if user_id:
            query["user_id"] = user_id
        if since:
            query["created_at"] = {"$gte": since}
        cursor = (
            db["mood_logs"]
            .find(query)
            .sort("created_at", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        items = [MoodLog(**doc) for doc in docs]
        return {"items": items, "count": len(items)}
    except Exception as e:
        logger.warning("MongoDB read for mood-logs failed, using in-memory: %s", e)
        # Fallback to in-memory logs
        logs = MOOD_LOGS
        if user_id:
            logs = [log for log in MOOD_LOGS if log.user_id == user_id]
        if since:
            logs = [log for log in logs if log.created_at >= since]
        logs_sorted = sorted(logs, key=lambda log: log.created_at, reverse=True)
        return {
            "items": logs_sorted[:limit],
            "count": min(len(logs_sorted), limit),
        }
