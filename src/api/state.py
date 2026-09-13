"""
Shared application state.

Routers import this module and access ``state.classifier`` / ``state.model_loaded``
so the startup handler can set these values once and every router sees the update.
"""

from typing import Any

# These are set by the lifespan handler in main.py after model loading.
classifier: Any = None
model_loaded: bool = False
