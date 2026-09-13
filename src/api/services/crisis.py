"""
Crisis detection service.

Uses keyword matching for conservative, high-recall crisis signal detection.
"""

from typing import List

CRISIS_KEYWORDS: List[str] = [
    "suicidal",
    "kill myself",
    "end my life",
    "can't go on",
    "no reason to live",
    "self-harm",
    "hurt myself",
]


def detect_crisis(text: str) -> bool:
    """Very conservative crisis signal detection based on keywords."""
    lowered = text.lower()
    return any(kw in lowered for kw in CRISIS_KEYWORDS)
