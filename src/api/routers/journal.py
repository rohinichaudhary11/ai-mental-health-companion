"""
Journal entry logging and emotion insight analysis.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter

from src.db import get_db
import src.api.state as state
from src.api.schemas import JournalEntry, JournalInsight

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api", tags=["Journal"])

# In-memory store fallback for demo or when DB is unavailable
JOURNAL_ENTRIES: List[JournalEntry] = []


@router.post("/journal", response_model=JournalInsight)
async def analyze_journal(entry: JournalEntry):
    """
    Save a private journal entry and return an emotional summary.
    """
    JOURNAL_ENTRIES.append(entry)

    # Best-effort persistence to MongoDB
    try:
        db = get_db()
        await db["journal_entries"].insert_one(entry.model_dump())
    except Exception as e:
        logger.warning("MongoDB insert for journal entry failed: %s", e)

    # Fetch user entries (prefer MongoDB if available)
    user_entries: List[JournalEntry]
    try:
        db = get_db()
        query: Dict[str, object] = {}
        if entry.user_id:
            query["user_id"] = entry.user_id
        cursor = (
            db["journal_entries"]
            .find(query)
            .sort("created_at", -1)
        )
        docs = await cursor.to_list(length=1000)
        user_entries = [JournalEntry(**doc) for doc in docs]
    except Exception:
        user_entries = [
            e for e in JOURNAL_ENTRIES if e.user_id == entry.user_id
        ]

    texts = [e.content for e in user_entries]
    emotions: List[str] = []
    confidences: List[float] = []

    if state.model_loaded and state.classifier is not None and texts:
        for text in texts:
            try:
                pred = state.classifier.predict(text, return_probs=False)
                emotions.append(pred["emotion"])
                confidences.append(pred["confidence"])
            except Exception as e:
                logger.warning("Error predicting emotion for journal text: %s", e)

    emotion_counts: Dict[str, int] = {}
    for e in emotions:
        emotion_counts[e] = emotion_counts.get(e, 0) + 1

    if emotion_counts:
        dominant = sorted(emotion_counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]
    else:
        dominant = "mixed"

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    patterns: List[str] = []
    if dominant in {"sadness", "fear"}:
        patterns.append("You seem to experience more low or anxious mood in many of your entries.")
    if dominant == "joy":
        patterns.append("There are frequent moments of joy in your writing—this is a strength you can build on.")

    # Weekday vs weekend heuristic
    weekday_stress_count = 0
    weekend_stress_count = 0
    for e in user_entries:
        weekday = e.created_at.weekday()
        if weekday < 5:
            weekday_stress_count += 1
        else:
            weekend_stress_count += 1
    if weekday_stress_count > weekend_stress_count + 1:
        patterns.append("Your entries suggest more difficult emotions on weekdays compared to weekends.")

    timeframe = "across your saved entries"
    summary_parts = [
        f"Across your journal, the most common emotional tone appears to be **{dominant}**.",
        f"The average confidence of the emotion model is approximately {avg_conf:.0%} (this is an estimate, not a diagnosis).",
    ]
    summary = " ".join(summary_parts)

    return JournalInsight(
        dominant_emotions=list(emotion_counts.keys()) or ["mixed"],
        summary=summary,
        patterns=patterns,
        timeframe=timeframe,
    )
