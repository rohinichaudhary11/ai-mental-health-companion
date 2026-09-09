import os
from typing import Optional
import certifi

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mental_health_companion")

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """
    Lazily create and return a shared MongoDB client.

    The client is designed to be reused across requests.
    """
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """Return the primary application database."""
    return get_client()[MONGODB_DB_NAME]


def get_collection(name: str):
    """Convenience helper to access a named collection."""
    return get_db()[name]
