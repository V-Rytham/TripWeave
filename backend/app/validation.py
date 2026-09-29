"""Pydantic validation at the API boundary.

Inputs are validated here BEFORE reaching LangGraph or external tools.
Pydantic validation is one layer (type/shape/length checks); it is not a
complete defense against prompt injection or all attacks — see README and
agent_adapter for additional handling (untrusted-data prefix, tool allowlist,
approval gate before email).
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

MAX_TEXT_LEN = 2000
MAX_LOCATION_LEN = 100
MIN_LOCATION_LEN = 2
MAX_PASSENGERS_TOTAL = 9
MAX_PROMPT_LEN = 2000

_LOCATION_RE = re.compile(r"^[A-Za-z][A-Za-z .,'\-()]{1,99}$")
_URL_RE = re.compile(r"https?://|www\.|\b(ssrf|file:|gopher:|dict:)", re.IGNORECASE)


class TripRequest(BaseModel):
    origin: str = Field(min_length=MIN_LOCATION_LEN, max_length=MAX_LOCATION_LEN)
    destination: str = Field(min_length=MIN_LOCATION_LEN, max_length=MAX_LOCATION_LEN)
    outbound_date: dt.date
    return_date: dt.date
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=9)
    hotel_class: Optional[int] = Field(default=None, ge=2, le=5)
    rooms: int = Field(default=1, ge=1, le=5)
    user_prompt: Optional[str] = Field(default=None, max_length=MAX_PROMPT_LEN)

    @field_validator("origin", "destination")
    @classmethod
    def _location_safe(cls, v: str) -> str:
        v = v.strip()
        if _URL_RE.search(v):
            raise ValueError("must not contain URLs or fetch directives")
        if len(v) > MAX_LOCATION_LEN:
            raise ValueError(f"must be at most {MAX_LOCATION_LEN} characters")
        if not _LOCATION_RE.match(v):
            raise ValueError("must be a plain place name (letters, spaces, basic punctuation)")
        return v

    @field_validator("user_prompt")
    @classmethod
    def _prompt_safe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) < 10:
            raise ValueError("user_prompt must be at least 10 characters if provided")
        if len(v) > MAX_PROMPT_LEN:
            raise ValueError(f"user_prompt must be at most {MAX_PROMPT_LEN} characters")
        return v

    @model_validator(mode="after")
    def _check_dates_and_counts(self) -> "TripRequest":
        today = dt.date.today()
        # Allow a small grace window for tests (yesterday) but reject distant past.
        if self.outbound_date < today - dt.timedelta(days=1):
            raise ValueError("outbound_date must not be in the past")
        if self.return_date <= self.outbound_date:
            raise ValueError("return_date must be after outbound_date")
        if (self.return_date - self.outbound_date).days > 60:
            raise ValueError("trip length must be at most 60 days")
        total = self.adults + self.children
        if total > MAX_PASSENGERS_TOTAL:
            raise ValueError(f"total passengers must be at most {MAX_PASSENGERS_TOTAL}")
        return self


class ApproveEmailRequest(BaseModel):
    itinerary_id: str = Field(min_length=8, max_length=64)
    from_email: EmailStr = Field(max_length=254)
    to_email: EmailStr = Field(max_length=254)
    subject: str = Field(min_length=1, max_length=200)

    @field_validator("subject")
    @classmethod
    def _subject_safe(cls, v: str) -> str:
        v = v.strip()
        if "\n" in v or "\r" in v:
            raise ValueError("subject must be a single line")
        return v
