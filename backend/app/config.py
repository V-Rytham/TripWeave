"""Backend configuration loaded from environment variables."""

from __future__ import annotations

import os


def _parse_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings:
    def __init__(self) -> None:
        self.allowed_origins: list[str] = _parse_origins(
            os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
        )
        self.mock_agent: bool = os.environ.get("MOCK_AGENT", "true").lower() in ("1", "true", "yes")
        self.mock_email: bool = os.environ.get("MOCK_EMAIL", "true").lower() in ("1", "true", "yes")
        self.backend_port: int = int(os.environ.get("BACKEND_PORT", "8000"))
        # Secrets are read lazily where needed; never exposed via API.
        # Names: OPENAI_API_KEY, SERPAPI_API_KEY, SENDGRID_API_KEY,
        # FROM_EMAIL, TO_EMAIL, EMAIL_SUBJECT


settings = Settings()
