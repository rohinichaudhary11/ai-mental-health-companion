"""
AI Therapist chat endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.db import get_db
import src.api.state as state
from src.api.schemas import ChatRequest, ChatResponse
from src.api.services.crisis import detect_crisis
from src.recommendations.engine import recommendation_engine

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api", tags=["Chat"])

CHAT_CONTEXT_LIMIT = 10


async def _get_recent_chat_messages(user_id: str, limit: int = CHAT_CONTEXT_LIMIT) -> List[Dict[str, object]]:
    """
    Fetch recent chat messages for a user from MongoDB.
    Returns messages in chronological order (oldest -> newest).
    """
    db = get_db()
    docs = await (
        db["chat_history"]
        .find({"user_id": user_id, "role": {"$in": ["user", "assistant"]}})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    docs.reverse()
    return [
        {
            "role": d.get("role"),
            "content": d.get("content"),
            "created_at": d.get("created_at"),
        }
        for d in docs
        if d.get("role") and d.get("content")
    ]


@router.post("/chat")
async def chat_therapist(request: ChatRequest):
    """
    Chat endpoint for emotional support and CBT-guided dialogue.
    """
    if not state.model_loaded or state.classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model is trained and available.",
        )

    try:
        if request.history:
            effective_history = [{"role": m.role, "content": m.content} for m in request.history]
        elif request.user_id:
            try:
                effective_history = await _get_recent_chat_messages(
                    request.user_id, CHAT_CONTEXT_LIMIT
                )
            except Exception as e:
                logger.warning("Failed to fetch chat history: %s", e)
                effective_history = []
        else:
            effective_history = []

        logger.info("Chat context size=%d", len(effective_history))

        # Check crisis signals
        crisis = detect_crisis(request.message)

        prediction = state.classifier.predict(request.message, return_probs=True)
        probabilities = prediction.get("probabilities", {}) or {}
        max_prob = max(probabilities.values()) if probabilities else 0.0

        if max_prob < 0.35:
            message = (
                "I couldn't clearly detect a specific emotional state. As an AI designed for emotional support, "
                "I cannot provide medical advice. If you are experiencing physical symptoms, please consult a professional."
            )
            if request.user_id:
                try:
                    db = get_db()
                    now = datetime.now(timezone.utc)
                    await db["chat_history"].insert_many(
                        [
                            {
                                "user_id": request.user_id,
                                "role": "user",
                                "content": request.message,
                                "created_at": now,
                            },
                            {
                                "user_id": request.user_id,
                                "role": "assistant",
                                "content": message,
                                "created_at": now,
                                "meta": {
                                    "emotion": "Uncertain",
                                    "confidence": max_prob,
                                    "state": "uncertain",
                                    "crisis_detected": crisis,
                                },
                            },
                        ]
                    )
                except Exception as e:
                    logger.warning("Failed to persist uncertain chat turn: %s", e)

            return {
                "status": "success",
                "state": "uncertain",
                "message": message,
                "confidence_score": max_prob,
                "crisis_detected": crisis,
            }

        predicted_emotion = prediction.get("emotion", "surprise")
        rec_result = recommendation_engine.get_recommendation(
            predicted_emotion,
            max_prob,
        )
        explanation = recommendation_engine.get_explanation(predicted_emotion)

        cbt_techniques: List[str] = []
        base_emotion = predicted_emotion.lower()
        if base_emotion in {"sadness", "fear", "anger", "stress"}:
            cbt_techniques.append(
                "Try writing down the thought that feels most distressing and then listing evidence for and against it."
            )
            cbt_techniques.append(
                "Notice and label thinking patterns such as all-or-nothing or catastrophizing and gently challenge them."
            )
        if base_emotion == "joy":
            cbt_techniques.append(
                "Capture what's going well in a gratitude journal so you can revisit it on harder days."
            )

        reply = (
            f"I hear that you're feeling **{predicted_emotion.capitalize()}** right now. "
            f"{explanation} {rec_result['recommendation']}"
        )

        if request.user_id:
            try:
                db = get_db()
                now = datetime.now(timezone.utc)
                await db["chat_history"].insert_many(
                    [
                        {
                            "user_id": request.user_id,
                            "role": "user",
                            "content": request.message,
                            "created_at": now,
                        },
                        {
                            "user_id": request.user_id,
                            "role": "assistant",
                            "content": reply,
                            "created_at": now,
                            "meta": {
                                "emotion": predicted_emotion,
                                "confidence": max_prob,
                                "state": "confident",
                                "crisis_detected": crisis,
                            },
                        },
                    ]
                )
            except Exception as e:
                logger.warning("Failed to persist chat turn: %s", e)

        return {
            "status": "success",
            "state": "confident",
            "emotion": predicted_emotion,
            "confidence_score": max_prob,
            "probabilities": probabilities,
            "reply": reply,
            "recommendation": rec_result["recommendation"],
            "cbt_techniques": cbt_techniques,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crisis_detected": crisis,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in chat endpoint: %s", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "An unexpected error occurred during chat processing."},
        )
