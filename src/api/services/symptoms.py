"""
Symptom classification and coping-technique service.

This is intentionally conservative and rule-based — it is NOT a diagnosis engine.
"""

from typing import List

from src.api.schemas import (
    CopingTechnique,
    DetectedCondition,
    EmergencyContact,
)


def classify_symptoms(text: str) -> List[DetectedCondition]:
    """Lightweight, rule-based symptom detection."""
    lowered = text.lower()
    conditions: List[DetectedCondition] = []

    if any(kw in lowered for kw in ["low bp", "low blood pressure", "dizzy", "faint", "lightheaded"]):
        conditions.append(
            DetectedCondition(
                name="Possible low blood pressure (hypotension)",
                likelihood="possible",
                explanation="Your description mentions dizziness or low blood pressure, which can be associated with hypotension.",
            )
        )

    if any(kw in lowered for kw in ["chest pain", "chest pressure", "tight chest"]):
        conditions.append(
            DetectedCondition(
                name="Chest discomfort",
                likelihood="potentially serious",
                explanation="Chest discomfort can be related to anxiety but may also indicate a serious medical issue.",
            )
        )

    if any(kw in lowered for kw in ["panic attack", "panic", "heart racing", "short of breath", "can't breathe"]):
        conditions.append(
            DetectedCondition(
                name="Possible panic or anxiety episode",
                likelihood="possible",
                explanation="Your message includes signs like intense fear or difficulty breathing, which can align with panic or anxiety.",
            )
        )

    if any(kw in lowered for kw in ["headache", "migraine"]):
        conditions.append(
            DetectedCondition(
                name="Headache or migraine",
                likelihood="possible",
                explanation="Mentions of persistent headache or migraine were detected.",
            )
        )

    if not conditions:
        conditions.append(
            DetectedCondition(
                name="Unclear condition",
                likelihood="uncertain",
                explanation="I couldn't confidently match your description to a specific condition, but I can still offer general support.",
            )
        )

    return conditions


def default_coping_for_condition(name: str) -> List[CopingTechnique]:
    """Return safe, generic coping steps for a detected condition name."""
    name_lower = name.lower()
    techniques: List[CopingTechnique] = []

    if "low blood pressure" in name_lower or "hypotension" in name_lower:
        techniques.append(
            CopingTechnique(
                title="Immediate steps for possible low blood pressure",
                steps=[
                    "Sit or lie down immediately to reduce the risk of falling.",
                    "If possible, elevate your legs slightly above heart level.",
                    "Drink water or an oral rehydration/electrolyte solution if you can.",
                    "Avoid standing up quickly or making sudden movements.",
                    "If symptoms are severe, persistent, or you feel like you might faint, seek urgent medical help.",
                ],
            )
        )

    if "chest discomfort" in name_lower:
        techniques.append(
            CopingTechnique(
                title="When experiencing chest discomfort",
                steps=[
                    "Stop physical activity and rest in a comfortable position.",
                    "Focus on slow, gentle breathing: inhale through your nose for 4 seconds, exhale through your mouth for 6 seconds.",
                    "Avoid self-diagnosing—chest pain can be serious.",
                    "If the pain is intense, spreads to your arm/jaw, or is accompanied by shortness of breath, sweating, or nausea, seek emergency medical help immediately.",
                ],
            )
        )

    if "panic" in name_lower or "anxiety" in name_lower:
        techniques.append(
            CopingTechnique(
                title="Grounding and breathing during intense anxiety",
                steps=[
                    "Try the 4-7-8 breathing technique: inhale for 4 seconds, hold for 7, exhale slowly for 8.",
                    "Use the 5-4-3-2-1 grounding exercise: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.",
                    "Remind yourself that panic symptoms, while scary, usually peak within minutes and then ease.",
                    "If episodes are frequent or worsening, contact a mental health professional or doctor.",
                ],
            )
        )

    if "headache" in name_lower or "migraine" in name_lower:
        techniques.append(
            CopingTechnique(
                title="Self-care for headache or migraine",
                steps=[
                    "Move to a quiet, darker room if possible.",
                    "Drink water to stay hydrated.",
                    "Avoid screens and bright lights for a while.",
                    "If you use prescribed medication for headaches or migraines, take it as directed.",
                    "Seek medical care if the headache is sudden and severe, follows a head injury, or differs from your usual pattern.",
                ],
            )
        )

    if not techniques:
        techniques.append(
            CopingTechnique(
                title="General self-care while unwell",
                steps=[
                    "Rest in a comfortable position and avoid strenuous activity.",
                    "Stay hydrated with water or clear fluids unless a doctor has told you otherwise.",
                    "Notice any changes or worsening of symptoms.",
                    "Contact a healthcare professional if you are concerned, unsure, or symptoms persist.",
                ],
            )
        )

    return techniques


def default_emergency_contacts() -> List[EmergencyContact]:
    """Generic emergency contacts (to be localised per deployment)."""
    return [
        EmergencyContact(
            name="Local Emergency Services",
            number="112 / 911 (region-specific)",
            description="Call immediately in life-threatening situations or severe symptoms.",
        ),
        EmergencyContact(
            name="Suicide & Crisis Helpline",
            number="Local/National helpline (configure per country)",
            description="24/7 support for suicidal thoughts, self-harm, or emotional crisis.",
        ),
        EmergencyContact(
            name="Mental Health Helpline",
            number="Check local mental health services",
            description="Non-emergency emotional support and guidance.",
        ),
    ]
