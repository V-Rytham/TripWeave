"""In-memory itinerary store (single-process demo)."""

from __future__ import annotations

import threading
import uuid
from typing import Any, Optional

_lock = threading.Lock()
_itineraries: dict[str, dict[str, Any]] = {}


def new_id() -> str:
    return uuid.uuid4().hex[:16]


def save(it: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        _itineraries[it["id"]] = it
        return it


def get(itinerary_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        item = _itineraries.get(itinerary_id)
        return dict(item) if item else None


def update(itinerary_id: str, **fields: Any) -> Optional[dict[str, Any]]:
    with _lock:
        if itinerary_id not in _itineraries:
            return None
        _itineraries[itinerary_id].update(fields)
        return dict(_itineraries[itinerary_id])


def clear() -> None:
    with _lock:
        _itineraries.clear()
