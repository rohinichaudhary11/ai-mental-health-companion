"""
Medical support and nearby care routing.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Request

from src.api.schemas import (
    CopingTechnique,
    MedicalLocation,
    SymptomSupportRequest,
    SymptomSupportResponse,
)
from src.api.services.crisis import detect_crisis
from src.api.services.medical import fetch_nearby_medical, lookup_ip_location
from src.api.services.symptoms import (
    classify_symptoms,
    default_coping_for_condition,
    default_emergency_contacts,
)

logger = logging.getLogger("mental_health_api")

router = APIRouter(prefix="/api", tags=["Medical"])


@router.post("/symptom-support", response_model=SymptomSupportResponse)
async def symptom_support(payload: SymptomSupportRequest, request: Request):
    """
    Provide symptom-aware, non-diagnostic support and first-aid style guidance.
    Always includes safety disclaimer and emergency resources.
    """
    crisis = detect_crisis(payload.text)
    detected_conditions = classify_symptoms(payload.text)

    coping: List[CopingTechnique] = []
    for c in detected_conditions:
        coping.extend(default_coping_for_condition(c.name))

    # Derive approximate location from client IP if available
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    nearby: List[MedicalLocation] = []
    if client_ip:
        loc = lookup_ip_location(client_ip)
        if loc:
            lat, lon = loc
            nearby = fetch_nearby_medical(lat, lon, radius_km=5.0)

    # Static fallback if live query yields no results
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


@router.post("/nearby-medical-support")
async def nearby_medical_support(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    query: Optional[str] = "hospital",
):
    """
    Return nearby hospitals/clinics/doctors using OpenStreetMap Overpass data.
    """
    if lat is None or lon is None:
        return {
            "items": [],
            "disclaimer": "Latitude and longitude are required for nearby search.",
        }

    locations = fetch_nearby_medical(lat, lon, radius_km=5.0)
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
