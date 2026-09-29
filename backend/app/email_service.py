"""Email sending with an explicit approval gate.

Generating or reviewing a plan must NEVER send email. Only
send_approved_email() sends, and it requires status == 'pending_review'.
"""

from __future__ import annotations

import os


class ApprovalRequiredError(Exception):
    pass


def send_approved_email(*, status: str, from_email: str, to_email: str, subject: str, html_body: str) -> dict:
    if status != "pending_review":
        raise ApprovalRequiredError("email requires explicit approval of a pending itinerary")
    mock = os.environ.get("MOCK_EMAIL", "true").lower() in ("1", "true", "yes")
    api_key = os.environ.get("SENDGRID_API_KEY")
    if mock or not api_key:
        # Reproducible stub: no network, no secrets.
        return {"provider": "mock", "sent": True, "to": to_email}
    # Real path: lazily import so mock environments don't need sendgrid.
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=html_body)
    sg = SendGridAPIClient(api_key)
    response = sg.send(message)
    return {"provider": "sendgrid", "sent": True, "status_code": response.status_code, "to": to_email}
