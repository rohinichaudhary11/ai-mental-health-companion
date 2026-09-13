"""
Analytics and personalized recommendation endpoints.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException

from src.db import get_db
import src.api.state as state
from src.api.schemas import (
    EmotionInsight,
    JournalEntry,
    MoodLog,
    PersonalizedRecommendation,
    PersonalizedRecommendationsResponse,
)
from src.api.routers.mood import MOOD_LOGS
from src.api.routers.journal import JOURNAL_ENTRIES

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api", tags=["Analytics"])


async def _compute_personalized_recommendations(
    user_id: str,
    timeframe_days: int = 30,
) -> PersonalizedRecommendationsResponse:
    """
    Analyze mood logs + chat history to generate personalized suggestions.
    """
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=timeframe_days)

    # Mood signals
    try:
        mood_docs = await (
            db["mood_logs"]
            .find({"user_id": user_id, "created_at": {"$gte": since}})
            .to_list(length=5000)
        )
    except Exception as e:
        logger.warning("Failed to query mood_logs for recommendations: %s", e)
        mood_docs = []

    mood_labels = [d.get("mood") for d in mood_docs if d.get("mood")]
    low_mood_count = sum(1 for m in mood_labels if m in {"very_low", "low"})

    # Chat emotion signals from assistant meta emotion in chat_history
    try:
        chat_docs = await (
            db["chat_history"]
            .find(
                {
                    "user_id": user_id,
                    "role": "assistant",
                    "created_at": {"$gte": since},
                }
            )
            .to_list(length=5000)
        )
    except Exception as e:
        logger.warning("Failed to query chat_history for recommendations: %s", e)
        chat_docs = []

    emotions = []
    for d in chat_docs:
        meta = d.get("meta") or {}
        e = meta.get("emotion")
        if isinstance(e, str):
            emotions.append(e.lower())

    stress_count = sum(1 for e in emotions if e == "stress")
    anxiety_count = sum(1 for e in emotions if e in {"fear", "anxiety"})

    signals = {
        "stress": stress_count,
        "anxiety": anxiety_count,
        "low_mood": low_mood_count,
    }

    recs: List[PersonalizedRecommendation] = []

    if stress_count + anxiety_count >= 5:
        recs.append(
            PersonalizedRecommendation(
                title="Stress & anxiety are showing up often",
                description=(
                    "Your recent mood/chat patterns suggest elevated stress or anxiety. "
                    "Short, consistent practices can help bring your nervous system down."
                ),
                actions=[
                    "Try a 3–5 minute breathing session (4-7-8 or box breathing).",
                    "Schedule one small recovery break today (walk, stretch, water).",
                    "Do a quick thought check: what is in my control right now?",
                ],
                severity="warning",
            )
        )
        recs.append(
            PersonalizedRecommendation(
                title="Meditation micro-habit",
                description="Start small: consistency matters more than duration.",
                actions=[
                    "Do 2 minutes of mindful breathing after waking up.",
                    "Use a guided meditation for anxiety (5–10 minutes).",
                    "If symptoms are intense or persistent, consider professional support.",
                ],
                severity="info",
            )
        )

    if low_mood_count >= 5:
        recs.append(
            PersonalizedRecommendation(
                title="Low mood check-in",
                description=(
                    "You've logged several low-mood check-ins recently. "
                    "Gentle structure can help during heavier weeks."
                ),
                actions=[
                    "Pick one manageable task and one soothing activity for today.",
                    "Reach out to a trusted person and share how you're doing.",
                    "Consider journaling: what would I say to a friend feeling this way?",
                ],
                severity="warning",
            )
        )

    if not recs:
        recs.append(
            PersonalizedRecommendation(
                title="Keep going",
                description="No major risk patterns detected in the recent window. Keep your check-ins consistent.",
                actions=[
                    "Log your mood daily for a week to spot trends.",
                    "Try one breathing session this week to build resilience.",
                ],
                severity="info",
            )
        )

    return PersonalizedRecommendationsResponse(
        user_id=user_id,
        timeframe_days=timeframe_days,
        signals=signals,
        recommendations=recs,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/recommendations/personalized", response_model=PersonalizedRecommendationsResponse)
async def personalized_recommendations(user_id: str, timeframe_days: int = 30):
    """
    Personalized recommendations based on stored mood logs and chat history.
    """
    try:
        return await _compute_personalized_recommendations(
            user_id=user_id,
            timeframe_days=timeframe_days,
        )
    except Exception as e:
        logger.error("Failed to generate recommendations: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations.",
        )


@router.get("/emotion-analysis", response_model=EmotionInsight)
async def emotion_analysis(user_id: Optional[str] = None):
    """
    Aggregate emotional insights from mood logs and journal entries.
    """
    try:
        db = get_db()
        mood_query: Dict[str, object] = {}
        journal_query: Dict[str, object] = {}
        if user_id:
            mood_query["user_id"] = user_id
            journal_query["user_id"] = user_id
        mood_docs = await db["mood_logs"].find(mood_query).to_list(length=5000)
        journal_docs = await db["journal_entries"].find(journal_query).to_list(length=5000)
        logs = [MoodLog(**doc) for doc in mood_docs]
        entries = [JournalEntry(**doc) for doc in journal_docs]
    except Exception:
        logs = (
            MOOD_LOGS
            if user_id is None
            else [log for log in MOOD_LOGS if log.user_id == user_id]
        )
        entries = (
            JOURNAL_ENTRIES
            if user_id is None
            else [e for e in JOURNAL_ENTRIES if e.user_id == user_id]
        )

    from_date = None
    to_date = None
    timestamps: List[datetime] = []

    for l in logs:
        timestamps.append(l.created_at)
    for e in entries:
        timestamps.append(e.created_at)

    if timestamps:
        from_date = min(timestamps)
        to_date = max(timestamps)

    emotion_counts: Dict[str, int] = {}
    confidences: List[float] = []
    if state.model_loaded and state.classifier is not None:
        for e in entries:
            try:
                pred = state.classifier.predict(e.content, return_probs=False)
                emotion_counts[pred["emotion"]] = emotion_counts.get(pred["emotion"], 0) + 1
                confidences.append(pred["confidence"])
            except Exception as ex:
                logger.warning("Error predicting emotion during analysis: %s", ex)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    notes: List[str] = []
    if emotion_counts:
        top = sorted(emotion_counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]
        notes.append(f"The most frequent emotion in your journal is **{top}**.")
    if len(entries) > 10:
        notes.append("You have built a consistent journaling habit—this is very helpful for reflection.")

    return EmotionInsight(
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        top_emotions=emotion_counts,
        average_confidence=avg_conf,
        notes=notes,
    )
