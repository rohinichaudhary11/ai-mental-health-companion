"""
Nearby-medical-support service.

Uses OpenStreetMap Overpass API and IP-based geolocation.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

import requests

from src.api.schemas import MedicalLocation

logger = logging.getLogger("mental_health_api")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in kilometres between two lat/lon points."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
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


# ---------------------------------------------------------------------------
# IP Geolocation
# ---------------------------------------------------------------------------

def lookup_ip_location(ip: str) -> Optional[Tuple[float, float]]:
    """
    Best-effort IP geolocation to derive (lat, lon).

    Uses HTTPS for privacy.  In production, replace with a more reliable,
    privacy-aware provider.
    """
    try:
        resp = requests.get(f"https://ip-api.com/json/{ip}", timeout=3)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != "success":
            return None
        lat, lon = data.get("lat"), data.get("lon")
        if lat is None or lon is None:
            return None
        return float(lat), float(lon)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Overpass query
# ---------------------------------------------------------------------------

def fetch_nearby_medical(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
    max_results: int = 10,
) -> List[MedicalLocation]:
    """Query OpenStreetMap Overpass API for nearby hospitals and clinics."""
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
        locations.append(
            MedicalLocation(
                name=name,
                address=_build_address(tags),
                contact_number=_extract_phone(tags),
                distance_km=round(distance, 2) if distance is not None else None,
                type="hospital" if loc_type == "hospital" else "clinic",
            )
        )

    locations.sort(key=lambda l: (l.distance_km is None, l.distance_km or 0.0))
    return locations[:max_results]
