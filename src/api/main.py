"""
FastAPI backend for emotion classification and recommendations.
Provides RESTful endpoints for real-time inference.
"""

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Tuple
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
import math
import requests
from enum import Enum
import os
import bcrypt
from jose import JWTError, jwt
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.inference.model_loader import load_classifier
from src.recommendations.engine import recommendation_engine
from src.db import get_db


SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "CHANGE_ME_TO_A_SECURE_RANDOM_VALUE",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mental_health_api")

# Initialize FastAPI app
app = FastAPI(
    title="Mental Health Companion API",
    description="AI-Powered Emotion Classification and Recommendation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
classifier = None
model_loaded = False


def _hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_access_token(data: Dict[str, object], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def _get_user_by_email(email: str) -> Optional["UserInDB"]:
    db = get_db()
    doc = await db["users"].find_one({"email": email})
    if not doc:
        return None
    # Map Mongo `_id` to `id`
    doc["id"] = str(doc.get("_id"))
    return UserInDB(**doc)


async def _authenticate_user(email: str, password: str) -> Optional["UserInDB"]:
    user = await _get_user_by_email(email)
    if not user:
        return None
    if not _verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> "UserPublic":
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_in_db = await _get_user_by_email(email)
    if user_in_db is None or user_in_db.id is None:
        raise credentials_exception

    return UserPublic(
        id=user_in_db.id,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        created_at=user_in_db.created_at,
    )


class PredictionRequest(BaseModel):
    """Request model for emotion prediction."""
    text: str = Field(..., description="User input text for emotion classification", min_length=1, max_length=1000)


class PredictionResponse(BaseModel):
    """Response model for emotion prediction."""
    emotion: str
    confidence: float
    probabilities: Dict[str, float]
    recommendation: str
    explanation: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    timestamp: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: str
    created_at: datetime


class UserPublic(UserBase):
    id: str
    created_at: datetime


@app.post("/api/auth/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    """
    Create a new user with a hashed password.
    """
    db = get_db()
    existing = await db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    now = datetime.utcnow()
    user_doc: Dict[str, object] = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": _hash_password(user.password),
        "created_at": now,
    }
    result = await db["users"].insert_one(user_doc)

    return UserPublic(
        id=str(result.inserted_id),
        email=user.email,
        full_name=user.full_name,
        created_at=now,
    )


@app.post("/api/auth/login", response_model=Token)
async def login(user: UserCreate):
    """
    Authenticate user and return a JWT access token.
    """
    auth_user = await _authenticate_user(user.email, user.password)
    if not auth_user or auth_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token(data={"sub": auth_user.email})
    return Token(access_token=access_token, token_type="bearer")


@app.get("/api/auth/me", response_model=UserPublic)
async def read_current_user(current_user: UserPublic = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    """
    return current_user


class MoodLabel(str, Enum):
    """High-level mood labels for tracking."""

    VERY_LOW = "very_low"
    LOW = "low"
    NEUTRAL = "neutral"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MoodLog(BaseModel):
    """Mood log entry for dashboard analytics."""

    user_id: Optional[str] = Field(None, description="User identifier (for multi-user deployments)")
    mood: MoodLabel = Field(..., description="Overall mood score for the entry")
    emoji: Optional[str] = Field(None, description="Emoji representation selected by the user")
    note: Optional[str] = Field(None, description="Optional free-text note")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JournalEntry(BaseModel):
    """Private mental health journal entry."""

    user_id: Optional[str] = Field(None, description="User identifier (for multi-user deployments)")
    title: Optional[str] = Field(None, description="Optional journal title")
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JournalInsight(BaseModel):
    """AI-generated summary of emotional patterns from journal entries."""

    dominant_emotions: List[str]
    summary: str
    patterns: List[str]
    timeframe: str


class EmotionInsight(BaseModel):
    """Aggregated emotional insight over a time range."""

    user_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    top_emotions: Dict[str, int]
    average_confidence: float
    notes: List[str] = []


class SymptomSupportRequest(BaseModel):
    """Request for symptom-aware medical assistance."""

    text: str = Field(..., description="User description of symptoms", min_length=1, max_length=1000)
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


# In-memory stores to simulate persistence.
# In production, these should be backed by MongoDB collections.
MOOD_LOGS: List[MoodLog] = []
JOURNAL_ENTRIES: List[JournalEntry] = []


CRISIS_KEYWORDS = [
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


def classify_symptoms(text: str) -> List[DetectedCondition]:
    """
    Lightweight, rule-based symptom detection.
    This is explicitly NOT a diagnosis engine.
    """
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
    """Generic emergency contacts (to be localized per deployment)."""
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


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CHAT_CONTEXT_LIMIT = 20


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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in kilometers between two lat/lon points."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _build_address(tags: Dict[str, str]) -> str:
    """Assemble a readable address from OSM tags."""
    parts: List[str] = []
    if "addr:street" in tags:
        street = tags["addr:street"]
        if "addr:housenumber" in tags:
            street = f"{tags['addr:housenumber']} {street}"
        parts.append(street)
    if "addr:city" in tags:
        parts.append(tags["addr:city"])
    if "addr:state" in tags:
        parts.append(tags["addr:state"])
    if "addr:postcode" in tags:
        parts.append(tags["addr:postcode"])
    if not parts and "addr:full" in tags:
        parts.append(tags["addr:full"])
    return ", ".join(parts) if parts else "Address not available"


def _extract_phone(tags: Dict[str, str]) -> Optional[str]:
    for key in ("phone", "contact:phone"):
        if key in tags:
            return tags[key]
    return None


def _lookup_ip_location(ip: str) -> Optional[Tuple[float, float]]:
    """
    Best-effort IP geolocation to derive (lat, lon).

    Uses a free, unauthenticated service; in production, replace
    with a more reliable, privacy-aware provider.
    """
    try:
        # ip-api.com has a generous free tier for non-commercial use.
        resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != "success":
            return None
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            return None
        return float(lat), float(lon)
    except Exception:
        return None


def _fetch_nearby_medical(
    lat: float, lon: float, radius_km: float = 5.0, max_results: int = 10
) -> List[MedicalLocation]:
    """
    Query OpenStreetMap Overpass API for nearby hospitals and clinics.

    Radius is in kilometers; Overpass expects meters.
    """
    radius_m = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:20];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      node["amenity"="clinic"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    try:
        resp = requests.post(OVERPASS_URL, data=query.encode("utf-8"), timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    elements = data.get("elements", [])
    locations: List[MedicalLocation] = []

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        el_lat = el.get("lat") or (el.get("center") or {}).get("lat")
        el_lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if el_lat is None or el_lon is None:
            continue
        try:
            distance = _haversine_km(lat, lon, float(el_lat), float(el_lon))
        except Exception:
            distance = None

        loc_type = tags.get("amenity", "hospital")
        address = _build_address(tags)
        phone = _extract_phone(tags)

        locations.append(
            MedicalLocation(
                name=name,
                address=address,
                contact_number=phone,
                distance_km=round(distance, 2) if distance is not None else None,
                type="hospital" if loc_type == "hospital" else "clinic",
            )
        )

    # Sort by distance and trim.
    locations.sort(key=lambda l: (l.distance_km is None, l.distance_km or 0.0))
    return locations[:max_results]


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


async def _compute_personalized_recommendations(user_id: str, timeframe_days: int = 30) -> PersonalizedRecommendationsResponse:
    """
    Analyze mood logs + chat history to generate simple personalized suggestions.

    This is intentionally heuristic and conservative.
    """
    db = get_db()
    since = datetime.utcnow() - timedelta(days=timeframe_days)

    # Mood signals
    mood_docs = await (
        db["mood_logs"]
        .find({"user_id": user_id, "created_at": {"$gte": since}})
        .to_list(length=5000)
    )
    mood_labels = [d.get("mood") for d in mood_docs if d.get("mood")]
    low_mood_count = sum(1 for m in mood_labels if m in {"very_low", "low"})

    # Chat emotion signals: use assistant meta emotion from chat_history
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
                    "You’ve logged several low-mood check-ins recently. "
                    "Gentle structure can help during heavier weeks."
                ),
                actions=[
                    "Pick one manageable task and one soothing activity for today.",
                    "Reach out to a trusted person and share how you’re doing.",
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
        generated_at=datetime.utcnow().isoformat(),
    )


@app.get(
    "/api/recommendations/personalized",
    response_model=PersonalizedRecommendationsResponse,
    tags=["Analytics"],
)
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@app.on_event("startup")
async def load_model():
    """Load model on startup."""
    global classifier, model_loaded
    try:
        model_path = Path("models")
        
        # Check if model files exist (look for config.json as indicator)
        if model_path.exists() and (model_path / "config.json").exists():
            classifier = load_classifier(str(model_path))
            model_loaded = True
            print("Model loaded successfully!")
        else:
            # Demo mode: Use pre-trained model from HuggingFace
            print("No fine-tuned model found. Using pre-trained DistilBERT for demo...")
            print("Note: For best results, train the model first using the training script.")
            try:
                from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
                import torch
                
                # Use a pre-trained emotion model or base DistilBERT
                model_name = "distilbert-base-uncased"
                tokenizer = DistilBertTokenizer.from_pretrained(model_name)
                
                # Create a simple classifier wrapper for demo
                class DemoClassifier:
                    def __init__(self, tokenizer):
                        self.tokenizer = tokenizer
                        # Include a dedicated "stress" label for stress-related phrases.
                        self.idx_to_emotion = {
                            0: 'joy',
                            1: 'sadness',
                            2: 'anger',
                            3: 'fear',
                            4: 'disgust',
                            5: 'surprise',
                            6: 'stress',
                        }
                    
                    def predict(self, text, return_probs=True, max_length=128):
                        # Simple rule-based demo prediction based on keywords
                        text_lower = text.lower()
                        emotion_keywords = {
                            'joy': [
                                'happy', 'joy', 'excited', 'great', 'wonderful',
                                'amazing', 'love', 'glad'
                            ],
                            'sadness': [
                                'sad', 'depressed', 'down', 'unhappy', 'lonely',
                                'crying', 'tears'
                            ],
                            'anger': [
                                'angry', 'mad', 'furious', 'annoyed',
                                'frustrated', 'irritated'
                            ],
                            # Fear remains focused on classic fear/anxiety words,
                            # while "stress" below handles explicit stress language.
                            'fear': [
                                'afraid', 'scared', 'worried', 'nervous',
                                'fear', 'terrified'
                            ],
                            'disgust': [
                                'disgusted', 'disgusting', 'revolting',
                                'gross', 'nasty'
                            ],
                            'surprise': [
                                'surprised', 'shocked', 'amazed',
                                'unexpected', 'wow'
                            ],
                            'stress': [
                                'stressed', 'stress', 'overwhelmed',
                                'overwhelming', 'under pressure',
                                'pressure', 'pressured',
                                'anxious', 'anxiety',
                                'tense', 'tension',
                                'burned out', 'burnt out',
                                'exhausted', 'overloaded'
                            ],
                        }
                        
                        scores: Dict[str, int] = {}
                        for emotion, keywords in emotion_keywords.items():
                            score = sum(1 for keyword in keywords if keyword in text_lower)
                            scores[emotion] = score
                        
                        total_score = sum(scores.values())
                        if total_score > 0:
                            probabilities = {
                                emotion: scores.get(emotion, 0) / total_score
                                for emotion in self.idx_to_emotion.values()
                            }
                        else:
                            # No obvious keywords: start from a uniform prior.
                            num_emotions = len(self.idx_to_emotion)
                            probabilities = {
                                emotion: 1.0 / num_emotions
                                for emotion in self.idx_to_emotion.values()
                            }
                        
                        # Get top emotion
                        predicted_emotion = max(probabilities, key=probabilities.get)
                        confidence = probabilities[predicted_emotion]
                        
                        result = {
                            'emotion': predicted_emotion,
                            'confidence': confidence
                        }
                        
                        if return_probs:
                            result['probabilities'] = probabilities
                        
                        return result
                
                classifier = DemoClassifier(tokenizer)
                model_loaded = True
                print("Demo mode activated! Using keyword-based emotion detection.")
            except Exception as demo_error:
                print(f"Error setting up demo mode: {demo_error}")
                model_loaded = False
    except Exception as e:
        print(f"Error loading model: {e}")
        model_loaded = False

    # Ensure essential MongoDB indexes exist (best-effort).
    try:
        db = get_db()
        await db["users"].create_index("email", unique=True)
        await db["mood_logs"].create_index([("user_id", 1), ("created_at", -1)])
        await db["journal_entries"].create_index([("user_id", 1), ("created_at", -1)])
        await db["chat_history"].create_index([("user_id", 1), ("created_at", -1)])
    except Exception:
        # Index creation failure should not block API startup.
        pass


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Mental Health Companion API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/healthcheck",
            "docs": "/docs"
        }
    }


@app.get("/healthcheck", response_model=HealthResponse, tags=["Health"])
async def healthcheck():
    """
    Health check endpoint.
    Returns API status and model availability.
    """
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        timestamp=datetime.now().isoformat()
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_emotion(request: PredictionRequest):
    """
    Predict emotion from user text and provide recommendation.
    
    Args:
        request: PredictionRequest with user text
    
    Returns:
        PredictionResponse with emotion, confidence, probabilities, recommendation, and explanation
    """
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model is trained and available."
        )

    text = request.text.strip()
    if len(text) < 3:
        raise HTTPException(
            status_code=400,
            detail="Input text must be at least 3 characters long."
        )
    
    try:
        start_time = time.time()
        logger.info("Prediction request received: text='%s'", text)
        
        # Predict emotion
        prediction = classifier.predict(text, return_probs=True)
        max_confidence = max(prediction["probabilities"].values())
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
                prediction['emotion'],
                prediction['confidence']
            )
            explanation = recommendation_engine.get_explanation(prediction['emotion'])
        
        # Calculate latency
        latency = time.time() - start_time
        
        response = PredictionResponse(
            emotion=prediction['emotion'],
            confidence=prediction['confidence'],
            probabilities=prediction['probabilities'],
            recommendation=rec_result['recommendation'],
            explanation=explanation,
            timestamp=datetime.now().isoformat()
        )
        
        # Log latency (in production, use proper logging)
        if latency > 0.5:
            print(f"Warning: High latency detected: {latency:.3f}s")
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during prediction: {str(e)}"
        )


@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(texts: list[str]):
    """
    Predict emotions for multiple texts (batch processing).
    
    Args:
        texts: List of text strings
    
    Returns:
        List of prediction results
    """
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please ensure the model is trained and available."
        )
    
    if len(texts) > 100:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Batch size too large. Maximum 100 texts per request."
        )
    
    try:
        predictions = classifier.predict_batch(texts)
        results = []
        
        for pred in predictions:
            rec_result = recommendation_engine.get_recommendation(
                pred['emotion'],
                pred['confidence']
            )
            
            results.append({
                'emotion': pred['emotion'],
                'confidence': pred['confidence'],
                'probabilities': pred['probabilities'],
                'recommendation': rec_result['recommendation'],
                'explanation': recommendation_engine.get_explanation(pred['emotion'])
            })
        
        return {
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during batch prediction: {str(e)}"
        )


@app.post("/api/mood-log", tags=["Mood"])
async def log_mood(entry: MoodLog):
    """
    Log a mood entry for a user.

    Entries are stored in memory and, when MongoDB is available,
    persisted to the `mood_logs` collection.
    """
    MOOD_LOGS.append(entry)

    # Best-effort persistence to MongoDB
    try:
        db = get_db()
        await db["mood_logs"].insert_one(entry.dict())
    except Exception:
        # Fail silently; the in-memory log still works for demo.
        pass

    return {"status": "ok", "logged_at": entry.created_at.isoformat()}


@app.get("/api/mood-log", tags=["Mood"])
async def get_mood_logs(
    user_id: Optional[str] = None,
    limit: int = 100,
    period: Optional[str] = None,
):
    """
    Return recent mood logs for a user (or all, if user_id is omitted).

    Prefers MongoDB when available, and falls back to in-memory logs.
    """
    period_lower = (period or "").lower().strip()
    since: Optional[datetime] = None
    if period_lower in {"week", "weekly", "7d", "7days"}:
        since = datetime.utcnow() - timedelta(days=7)
    elif period_lower in {"month", "monthly", "30d", "30days"}:
        since = datetime.utcnow() - timedelta(days=30)

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
    except Exception:
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


@app.post("/api/journal", response_model=JournalInsight, tags=["Journal"])
async def analyze_journal(entry: JournalEntry):
    """
    Save a private journal entry and return an emotional summary.

    This uses simple heuristics plus the existing emotion classifier to
    highlight patterns. In production, entries should be encrypted at rest.
    """
    JOURNAL_ENTRIES.append(entry)

    # Best-effort persistence to MongoDB
    try:
        db = get_db()
        await db["journal_entries"].insert_one(entry.dict())
    except Exception:
        pass

    # Naive emotional pattern extraction across all entries for this user.
    # Prefer MongoDB if available.
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

    if model_loaded and texts:
        for text in texts:
            pred = classifier.predict(text, return_probs=False)
            emotions.append(pred["emotion"])
            confidences.append(pred["confidence"])

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


@app.get("/api/emotion-analysis", response_model=EmotionInsight, tags=["Analytics"])
async def emotion_analysis(user_id: Optional[str] = None):
    """
    Aggregate emotional insights from mood logs and journal entries.

    This endpoint is designed for dashboard analytics.
    """
    # Prefer MongoDB where possible and fall back to in-memory data.
    try:
        db = get_db()
        mood_query: Dict[str, object] = {}
        journal_query: Dict[str, object] = {}
        if user_id:
            mood_query["user_id"] = user_id
            journal_query["user_id"] = user_id
        mood_docs = await db["mood_logs"].find(mood_query).to_list(length=5000)
        journal_docs = await db["journal_entries"].find(journal_query).to_list(
            length=5000
        )
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

    # Basic emotion counts re-using classifier on journal entries.
    emotion_counts: Dict[str, int] = {}
    confidences: List[float] = []
    if model_loaded:
        for e in entries:
            pred = classifier.predict(e.content, return_probs=False)
            emotion_counts[pred["emotion"]] = emotion_counts.get(pred["emotion"], 0) + 1
            confidences.append(pred["confidence"])

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


@app.post("/api/symptom-support", response_model=SymptomSupportResponse, tags=["Medical"])
async def symptom_support(payload: SymptomSupportRequest, request: Request):
    """
    Provide symptom-aware, non-diagnostic support and first-aid style guidance.

    This endpoint is intentionally conservative and always includes a medical disclaimer.
    """
    crisis = detect_crisis(payload.text)
    detected_conditions = classify_symptoms(payload.text)

    coping: List[CopingTechnique] = []
    for c in detected_conditions:
        coping.extend(default_coping_for_condition(c.name))

    # Try to infer the user's approximate location from their IP address.
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else None

    nearby: List[MedicalLocation] = []
    if client_ip:
        loc = _lookup_ip_location(client_ip)
        if loc:
            lat, lon = loc
            nearby = _fetch_nearby_medical(lat, lon, radius_km=5.0)

    # Fallback to illustrative static data if Overpass or geolocation fails.
    if not nearby:
        nearby = [
            MedicalLocation(
                name="City General Hospital",
                address="123 Wellness Avenue",
                contact_number="+1-000-000-0000",
                distance_km=2.1,
                type="hospital",
            ),
            MedicalLocation(
                name="Calm Minds Mental Health Clinic",
                address="45 Serenity Street",
                contact_number="+1-000-000-0001",
                distance_km=3.4,
                type="clinic",
            ),
        ]

    disclaimer = (
        "This information is for guidance only and is not a medical diagnosis. "
        "Always consult a doctor or qualified health professional for medical concerns."
    )

    return SymptomSupportResponse(
        detected_conditions=detected_conditions,
        coping_techniques=coping,
        nearby_support=nearby,
        emergency_contacts=default_emergency_contacts(),
        disclaimer=disclaimer,
        crisis_detected=crisis,
    )


@app.post("/api/nearby-medical-support", tags=["Medical"])
async def nearby_medical_support(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    query: Optional[str] = "hospital",
):
    """
    Return nearby hospitals/clinics/doctors using OpenStreetMap Overpass data.

    If `lat`/`lon` are not provided, this endpoint will simply return an
    empty list; `symptom-support` is responsible for IP-based fallback.
    """
    if lat is None or lon is None:
        return {"items": [], "disclaimer": "Latitude and longitude are required for nearby search."}

    locations = _fetch_nearby_medical(lat, lon, radius_km=5.0)
    return {
        "items": [
            {
                "name": loc.name,
                "address": loc.address,
                "contact_number": loc.contact_number,
                "distance_km": loc.distance_km,
                "type": loc.type,
            }
            for loc in locations
        ],
        "disclaimer": "Results are sourced from OpenStreetMap via Overpass and may be incomplete.",
    }


@app.post("/api/chat", tags=["Chat"])
async def chat_therapist(request: ChatRequest):
    if not model_loaded:
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
            except Exception:
                effective_history = []
        else:
            effective_history = []
        logger.info("Chat context size=%d", len(effective_history))
        prediction = classifier.predict(request.message, return_probs=True)
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
                    now = datetime.utcnow()
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
                                },
                            },
                        ]
                    )
                except Exception:
                    pass
            return {
                "status": "success",
                "state": "uncertain",
                "message": message,
                "confidence_score": max_prob,
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
                now = datetime.utcnow()
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
                            },
                        },
                    ]
                )
            except Exception:
                pass
        return {
            "status": "success",
            "state": "confident",
            "emotion": predicted_emotion,
            "confidence_score": max_prob,
            "probabilities": probabilities,
            "reply": reply,
            "recommendation": rec_result["recommendation"],
            "cbt_techniques": cbt_techniques,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal server error", "detail": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

