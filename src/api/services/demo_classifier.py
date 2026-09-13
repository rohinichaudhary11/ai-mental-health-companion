"""
Demo keyword-based emotion classifier.

Used as a fallback when no fine-tuned DistilBERT model is available.
"""

from typing import Dict, List


class DemoClassifier:
    """Keyword-based emotion classifier for demo / fallback mode."""

    def __init__(self) -> None:
        self.idx_to_emotion: Dict[int, str] = {
            0: "joy",
            1: "sadness",
            2: "anger",
            3: "fear",
            4: "disgust",
            5: "surprise",
            6: "stress",
        }
        self._emotion_keywords: Dict[str, List[str]] = {
            "joy": [
                "happy", "joy", "excited", "great", "wonderful",
                "amazing", "love", "glad",
            ],
            "sadness": [
                "sad", "depressed", "down", "unhappy", "lonely",
                "crying", "tears",
            ],
            "anger": [
                "angry", "mad", "furious", "annoyed",
                "frustrated", "irritated",
            ],
            "fear": [
                "afraid", "scared", "worried", "nervous",
                "fear", "terrified",
            ],
            "disgust": [
                "disgusted", "disgusting", "revolting",
                "gross", "nasty",
            ],
            "surprise": [
                "surprised", "shocked", "amazed",
                "unexpected", "wow",
            ],
            "stress": [
                "stressed", "stress", "overwhelmed", "overwhelming",
                "under pressure", "pressure", "pressured",
                "anxious", "anxiety", "tense", "tension",
                "burned out", "burnt out", "exhausted", "overloaded",
            ],
        }

    # -----------------------------------------------------------------------
    # Public API (same interface as EmotionClassifier)
    # -----------------------------------------------------------------------

    def predict(
        self,
        text: str,
        return_probs: bool = True,
        max_length: int = 128,
    ) -> Dict:
        """Predict the dominant emotion from *text* using keyword matching."""
        text_lower = text.lower()

        scores: Dict[str, int] = {}
        for emotion, keywords in self._emotion_keywords.items():
            scores[emotion] = sum(1 for kw in keywords if kw in text_lower)

        total = sum(scores.values())
        if total > 0:
            probabilities = {
                e: scores.get(e, 0) / total
                for e in self.idx_to_emotion.values()
            }
        else:
            n = len(self.idx_to_emotion)
            probabilities = {e: 1.0 / n for e in self.idx_to_emotion.values()}

        predicted = max(probabilities, key=probabilities.get)  # type: ignore[arg-type]
        result: Dict = {"emotion": predicted, "confidence": probabilities[predicted]}
        if return_probs:
            result["probabilities"] = probabilities
        return result

    def predict_batch(
        self,
        texts: List[str],
        max_length: int = 128,
    ) -> List[Dict]:
        """Predict emotions for a batch of texts."""
        return [self.predict(t, return_probs=True, max_length=max_length) for t in texts]
