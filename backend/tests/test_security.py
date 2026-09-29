"""Security tests: approval gate, oversized rejection, no secret leakage."""

import datetime as dt
import io
import logging
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("MOCK_AGENT", "true")
os.environ.setdefault("MOCK_EMAIL", "true")
os.environ["SENDGRID_API_KEY"] = "SECRET-SHOULD-NEVER-LEAK"
os.environ["OPENAI_API_KEY"] = "SECRET-OPENAI-NEVER-LEAK"

from fastapi.testclient import TestClient

from backend.app import metrics, store
from backend.app.email_service import ApprovalRequiredError, send_approved_email
from backend.app.main import app

client = TestClient(app)


def _gql(query):
    return client.post("/graphql", json={"query": query})


def _dates(days_out=30, length=6):
    out = (dt.date.today() + dt.timedelta(days=days_out)).isoformat()
    ret = (dt.date.today() + dt.timedelta(days=days_out + length)).isoformat()
    return out, ret


def test_oversized_request_rejected():
    out, ret = _dates()
    big = "x" * 5000
    q = 'mutation { createItinerary(input: {origin:"Madrid", destination:"Paris", outboundDate:"%s", returnDate:"%s", userPrompt:"%s"}) { id } }' % (out, ret, big)
    r = _gql(q)
    assert r.status_code == 200
    assert r.json().get("errors"), "oversized prompt must produce GraphQL errors"


def test_invalid_dates_rejected():
    out, ret = _dates()
    q = 'mutation { createItinerary(input: {origin:"Madrid", destination:"Paris", outboundDate:"%s", returnDate:"%s"}) { id } }' % (ret, out)
    r = _gql(q)
    assert r.json().get("errors")


def test_approval_required_before_email():
    # Direct service gate: wrong status must raise.
    try:
        send_approved_email(status="draft", from_email="a@x.com", to_email="b@x.com",
                            subject="s", html_body="<p>hi</p>")
        assert False, "should have raised"
    except ApprovalRequiredError:
        pass


def test_full_flow_requires_approval_and_hides_secrets(caplog):
    store.clear()
    metrics.clear()
    out, ret = _dates()
    q = 'mutation { createItinerary(input: {origin:"Madrid", destination:"Paris", outboundDate:"%s", returnDate:"%s"}) { id status emailStatus } }' % (out, ret)
    r = _gql(q).json()
    assert "data" in r and r["data"]["createItinerary"]["status"] == "pending_review"
    assert r["data"]["createItinerary"]["emailStatus"] == "not_sent"
    body = str(r)
    assert "SECRET-SHOULD-NEVER-LEAK" not in body
    assert "SECRET-OPENAI-NEVER-LEAK" not in body


def test_no_secrets_in_logs(caplog):
    # Generating an itinerary must not log secrets or full email contents.
    store.clear()
    out, ret = _dates()
    with caplog.at_level(logging.INFO):
        q = 'mutation { createItinerary(input: {origin:"Madrid", destination:"Paris", outboundDate:"%s", returnDate:"%s"}) { id } }' % (out, ret)
        _gql(q)
    text = "".join(getattr(rec, "message", "") for rec in caplog.records)
    assert "SECRET-SHOULD-NEVER-LEAK" not in text
    assert "SECRET-OPENAI-NEVER-LEAK" not in text
