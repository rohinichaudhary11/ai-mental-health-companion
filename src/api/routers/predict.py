"""
Emotion prediction endpoints (single and batch).
"""

import logging
import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

import src.api.state as state
from src.api.schemas import PredictionRequest, PredictionResponse
from src.recommendations.engine import recommendation_engine

logger = logging.getLogger("mental_health_api")

router = APIRouter(tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_emotion(request: PredictionRequest):
    """
    Predict emotion from user text and provide recommendation.
    """
    if not state.model_loaded or state.classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model is trained and available.",
        )

    text = request.text.strip()
    if len(text) < 3:
        raise HTTPException(
            status_code=400,
            detail="Input text must be at least 3 characters long.",
        )

    try:
        start_time = time.time()
        logger.info("Prediction request received: text='%s'", text)

        # Predict emotion
        prediction = state.classifier.predict(text, return_probs=True)
        max_confidence = max(prediction["probabilities"].values()) if prediction.get("probabilities") else prediction.get("confidence", 0.0)
        logger.info("Prediction max_confidence=%.4f", max_confidence)

        if max_confidence < 0.35:
            prediction["emotion"] = "Uncertain"
            prediction["confidence"] = max_confidence

        # Get recommendation
        if prediction["emotion"] == "Uncertain":
            rec_result = {
                "recommendation": (
                    "I couldn't clearly detect a specific emotional state. "
                    "As an AI designed for emotional support, I cannot provide medical advice. "
                    "If you are experiencing physical symptoms, please consult a professional."
                )
            }
            explanation = "The model confidence is below the uncertainty threshold."
        else:
            rec_result = recommendation_engine.get_recommendation(
                prediction["emotion"],
                prediction["confidence"],
            )
            explanation = recommendation_engine.get_explanation(prediction["emotion"])

        latency = time.time() - start_time
        if latency > 0.5:
            logger.warning("High latency detected in prediction: %.3fs", latency)

        return PredictionResponse(
            emotion=prediction["emotion"],
            confidence=prediction["confidence"],
            probabilities=prediction.get("probabilities", {}),
            recommendation=rec_result["recommendation"],
            explanation=explanation,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during prediction: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during prediction processing.",
        )


@router.post("/predict/batch")
async def predict_batch(texts: List[str]):
    """
    Predict emotions for multiple texts (batch processing).
    """
    if not state.model_loaded or state.classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model is trained and available.",
        )

    if len(texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size too large. Maximum 100 texts per request.",
        )

    try:
        predictions = state.classifier.predict_batch(texts)
        results = []

        for pred in predictions:
            rec_result = recommendation_engine.get_recommendation(
                pred["emotion"],
                pred["confidence"],
            )

            results.append({
                "emotion": pred["emotion"],
                "confidence": pred["confidence"],
                "probabilities": pred.get("probabilities", {}),
                "recommendation": rec_result["recommendation"],
                "explanation": recommendation_engine.get_explanation(pred["emotion"]),
            })

        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during batch prediction: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during batch prediction processing.",
        )
