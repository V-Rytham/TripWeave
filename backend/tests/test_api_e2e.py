"""Documented end-to-end path using mocks: create -> review -> approve."""

import datetime as dt
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

os.environ.setdefault("MOCK_AGENT", "true")
os.environ.setdefault("MOCK_EMAIL", "true")

from fastapi.testclient import TestClient

from backend.app import metrics, store
from backend.app.main import app

client = TestClient(app)


def test_e2e_create_review_approve():
    store.clear()
    metrics.clear()
    out = (dt.date.today() + dt.timedelta(days=30)).isoformat()
    ret = (dt.date.today() + dt.timedelta(days=36)).isoformat()
    create = client.post("/graphql", json={"query": (
        'mutation { createItinerary(input: {origin:"Madrid", destination:"Tokyo", '
        'outboundDate:"%s", returnDate:"%s", adults:2, hotelClass:4}) '
        '{ id status summary generationTimeMs emailStatus flights { airline price currency } '
        'hotels { name rating totalPrice } } }' % (out, ret)
    )}).json()
    assert "errors" not in create, create
    it = create["data"]["createItinerary"]
    assert it["status"] == "pending_review"
    assert it["generationTimeMs"] >= 0
    assert len(it["flights"]) == 2
    assert len(it["hotels"]) == 2
    iid = it["id"]

    # Review step: fetch by id (no email sent yet).
    got = client.post("/graphql", json={"query": '{ itinerary(id:"%s") { id status emailStatus summary } }' % iid}).json()
    assert got["data"]["itinerary"]["status"] == "pending_review"
    assert got["data"]["itinerary"]["emailStatus"] == "not_sent"

    # Approval step: explicit user action sends (mock) email.
    approved = client.post("/graphql", json={"query": (
        'mutation { approveItinerary(input: {itineraryId:"%s", fromEmail:"a@example.com", '
        'toEmail:"b@example.com", subject:"Trip plan"}) { id status emailStatus } }' % iid
    )}).json()
    assert "errors" not in approved, approved
    assert approved["data"]["approveItinerary"]["status"] == "email_sent"
    assert approved["data"]["approveItinerary"]["emailStatus"] in ("sent", "mock_sent")

    # Metrics recorded exactly one generation (email excluded from generation time).
    m = client.post("/graphql", json={"query": "{ metricsSummary { count medianMs p95Ms errorRate } }"}).json()
    assert m["data"]["metricsSummary"]["count"] >= 1
