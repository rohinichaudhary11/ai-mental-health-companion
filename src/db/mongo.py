import os
import logging
from typing import Optional

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Load .env for local development (no-op if file does not exist)
load_dotenv()

logger = logging.getLogger("mental_health_api")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip().strip('"').strip("'")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "mental_health_companion").strip().strip('"').strip("'")

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """
    Lazily create and return a shared MongoDB client.

    The client is designed to be reused across requests.
    """
    global _client
    if _client is None:
        logger.info("Creating new MongoDB client for URI: %s…", MONGODB_URI[:30])
        _client = AsyncIOMotorClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
        )
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """Return the primary application database."""
    return get_client()[MONGODB_DB_NAME]


def get_collection(name: str):
    """Convenience helper to access a named collection."""
    return get_db()[name]


async def close_client() -> None:
    """Close the MongoDB client connection (call during shutdown)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed.")
