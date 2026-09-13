"""
Pydantic models (request / response schemas) for the Mental Health Companion API.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # fallback if email-validator package is not installed


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Request model for emotion prediction."""
    text: str = Field(
        ...,
        description="User input text for emotion classification",
        min_length=1,
        max_length=1000,
    )


class PredictionResponse(BaseModel):
    """Response model for emotion prediction."""
    emotion: str
    confidence: float
    probabilities: Dict[str, float]
    recommendation: str
    explanation: str
    timestamp: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    database_connected: bool = False
    database_status: str = "disconnected"
    database_error: Optional[str] = None
    timestamp: str


# ---------------------------------------------------------------------------
# Auth / Users
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserInDB(UserBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[str] = None
    hashed_password: str
    created_at: datetime


class UserPublic(UserBase):
    id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Mood
# ---------------------------------------------------------------------------

class MoodLabel(str, Enum):
    """High-level mood labels for tracking."""
    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MoodLog(BaseModel):
    """Mood log entry for dashboard analytics."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: Optional[str] = Field(None, description="User identifier")
    mood: MoodLabel = Field(..., description="Overall mood score for the entry")
    emoji: Optional[str] = Field(None, description="Emoji representation")
    note: Optional[str] = Field(None, description="Optional free-text note")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------

class JournalEntry(BaseModel):
    """Private mental health journal entry."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: Optional[str] = Field(None, description="User identifier")
    title: Optional[str] = Field(None, description="Optional journal title")
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JournalInsight(BaseModel):
    """AI-generated summary of emotional patterns from journal entries."""
    dominant_emotions: List[str]
    summary: str
    patterns: List[str]
    timeframe: str


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class EmotionInsight(BaseModel):
    """Aggregated emotional insight over a time range."""
    user_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    top_emotions: Dict[str, int]
    average_confidence: float
    notes: List[str] = []


class PersonalizedRecommendation(BaseModel):
    """Personalized dashboard recommendation derived from history."""
    title: str
    description: str
    actions: List[str]
    severity: str = "info"  # info | warning


class PersonalizedRecommendationsResponse(BaseModel):
    user_id: str
    timeframe_days: int
    signals: Dict[str, int]
    recommendations: List[PersonalizedRecommendation]
    generated_at: str


# ---------------------------------------------------------------------------
# Symptom / Medical support
# ---------------------------------------------------------------------------

class SymptomSupportRequest(BaseModel):
    """Request for symptom-aware medical assistance."""
    text: str = Field(
        ...,
        description="User description of symptoms",
        min_length=1,
        max_length=1000,
    )
    user_id: Optional[str] = None


class DetectedCondition(BaseModel):
    """Detected condition based on symptom description."""
    name: str
    likelihood: str
    explanation: str


class CopingTechnique(BaseModel):
    """Safe coping or first-aid technique."""
    title: str
    steps: List[str]


class MedicalLocation(BaseModel):
    """Nearby medical support location."""
    name: str
    address: str
    contact_number: Optional[str] = None
    distance_km: Optional[float] = None
    type: str = Field(..., description="hospital, clinic, or doctor")


class EmergencyContact(BaseModel):
    """Emergency support contact."""
    name: str
    number: str
    description: Optional[str] = None


class SymptomSupportResponse(BaseModel):
    """Response payload for symptom-aware support and nearby care."""
    detected_conditions: List[DetectedCondition]
    coping_techniques: List[CopingTechnique]
    nearby_support: List[MedicalLocation]
    emergency_contacts: List[EmergencyContact]
    disclaimer: str
    crisis_detected: bool = False


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """Single message within a chat turn."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Rich chat request that includes history and metadata."""
    user_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """Chat therapist response with emotion, CBT techniques, and optional medical panel."""
    reply: str
    emotion: str
    confidence: float
    probabilities: Dict[str, float]
    cbt_techniques: List[str]
    recommendation: str
    explanation: str
    timestamp: str
    crisis_detected: bool = False
    crisis_message: Optional[str] = None
    symptom_support: Optional[SymptomSupportResponse] = None
