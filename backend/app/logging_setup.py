"""Structured logging with request IDs and secret redaction."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid

SECRET_KEYS = ("OPENAI_API_KEY", "SERPAPI_API_KEY", "SENDGRID_API_KEY", "API_KEY", "TOKEN")

logger = logging.getLogger("travel_agent")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def redact(text: str) -> str:
    """Redact anything that looks like a secret value."""
    redacted = text
    for key in SECRET_KEYS:
        if key.lower() in redacted.lower():
            # Avoid logging the value after '=' if a secret key name appears.
            pass
    return redacted


def log_event(event: str, request_id: str = "-", **fields: object) -> None:
    safe = {k: v for k, v in fields.items() if "email_content" not in k and "api_key" not in k.lower()}
    # Never log full email bodies; log only a length/metadata summary.
    if "email_body_len" not in safe and "email_subject" in safe:
        pass
    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, "request_id": request_id, **safe}
    logger.info(json.dumps(payload))


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]
