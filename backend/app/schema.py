"""GraphQL schema (primary frontend API) built with Strawberry."""

from __future__ import annotations

import datetime as dt
from typing import Optional

import strawberry
from strawberry.types import Info

from . import metrics, store
from .agent_adapter import generate_itinerary
from .email_service import ApprovalRequiredError, send_approved_email
from .logging_setup import log_event
from .validation import ApproveEmailRequest, TripRequest


@strawberry.type
class FlightOption:
    airline: str
    departure: str
    arrival: str
    price: float
    currency: str
    booking_url: Optional[str] = None
    logo_url: Optional[str] = None


@strawberry.type
class HotelOption:
    name: str
    description: str
    price_per_night: float
    total_price: float
    currency: str
    rating: float
    website_url: Optional[str] = None
    image_url: Optional[str] = None


@strawberry.type
class Itinerary:
    id: str
    status: str  # pending_review | approved | email_sent | failed
    summary: str
    flights: list[FlightOption]
    hotels: list[HotelOption]
    generation_time_ms: float
    created_at: str
    email_status: str  # not_sent | sent | mock_sent | failed


@strawberry.type
class MetricsSummary:
    count: int
    median_ms: float
    p95_ms: float
    error_rate: float


@strawberry.input
class TripRequestInput:
    origin: str
    destination: str
    outbound_date: str  # YYYY-MM-DD; validated via Pydantic
    return_date: str
    adults: int = 1
    children: int = 0
    hotel_class: Optional[int] = None
    rooms: int = 1
    user_prompt: Optional[str] = None


@strawberry.input
class ApproveEmailInput:
    itinerary_id: str
    from_email: str
    to_email: str
    subject: str = "Your travel itinerary"


def _to_gql(item: dict) -> Itinerary:
    return Itinerary(
        id=item["id"],
        status=item["status"],
        summary=item["summary"],
        flights=[FlightOption(**f) for f in item.get("flights", [])],
        hotels=[HotelOption(**h) for h in item.get("hotels", [])],
        generation_time_ms=item.get("generation_time_ms", 0.0),
        created_at=item.get("created_at", ""),
        email_status=item.get("email_status", "not_sent"),
    )


def _parse_request(inp: TripRequestInput) -> TripRequest:
    # Pydantic enforces all limits/dates before LangGraph/tools.
    return TripRequest(
        origin=inp.origin,
        destination=inp.destination,
        outbound_date=dt.date.fromisoformat(inp.outbound_date),
        return_date=dt.date.fromisoformat(inp.return_date),
        adults=inp.adults,
        children=inp.children,
        hotel_class=inp.hotel_class,
        rooms=inp.rooms,
        user_prompt=inp.user_prompt,
    )


@strawberry.type
class Query:
    @strawberry.field
    def itinerary(self, info: Info, id: str) -> Optional[Itinerary]:
        item = store.get(id)
        return _to_gql(item) if item else None

    @strawberry.field
    def metrics_summary(self, info: Info) -> MetricsSummary:
        s = metrics.summary()
        return MetricsSummary(count=s["count"], median_ms=s["median_ms"], p95_ms=s["p95_ms"], error_rate=s["error_rate"])


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_itinerary(self, info: Info, input: TripRequestInput) -> Itinerary:
        request_id = info.context.get("request_id", "-") if isinstance(info.context, dict) else "-"
        req = _parse_request(inp=input)
        start = metrics.now()
        try:
            gen = generate_itinerary(req)
        except Exception:
            metrics.record_latency(metrics.elapsed_seconds(start, metrics.now()), ok=False)
            raise
        elapsed_ms = metrics.elapsed_seconds(start, metrics.now()) * 1000.0
        metrics.record_latency(elapsed_ms / 1000.0, ok=True)
        item = {
            "id": store.new_id(),
            "status": "pending_review",
            "summary": gen["summary"],
            "flights": gen["flights"],
            "hotels": gen["hotels"],
            "generation_time_ms": round(elapsed_ms, 2),
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "email_status": "not_sent",
            "thread_id": gen.get("thread_id", ""),
            "origin": req.origin,
            "destination": req.destination,
        }
        store.save(item)
        # Log metadata only: no API keys, no full email contents, minimal PII.
        log_event("itinerary_created", request_id=request_id, itinerary_id=item["id"],
                  origin_len=len(req.origin), destination_len=len(req.destination),
                  generation_time_ms=item["generation_time_ms"])
        return _to_gql(item)

    @strawberry.mutation
    def approve_itinerary(self, info: Info, input: ApproveEmailInput) -> Itinerary:
        request_id = info.context.get("request_id", "-") if isinstance(info.context, dict) else "-"
        approved = ApproveEmailRequest(
            itinerary_id=input.itinerary_id, from_email=input.from_email,
            to_email=input.to_email, subject=input.subject,
        )
        item = store.get(approved.itinerary_id)
        if item is None:
            raise ValueError("itinerary not found")
        if item["status"] != "pending_review":
            raise ApprovalRequiredError("itinerary is not awaiting approval")
        html_body = f"<html><body><h2>Your itinerary</h2><p>{item['summary']}</p></body></html>"
        try:
            result = send_approved_email(
                status=item["status"], from_email=str(approved.from_email),
                to_email=str(approved.to_email), subject=approved.subject, html_body=html_body,
            )
        except ApprovalRequiredError:
            raise
        email_status = "mock_sent" if result.get("provider") == "mock" else "sent"
        updated = store.update(item["id"], status="email_sent", email_status=email_status)
        log_event("itinerary_approved", request_id=request_id, itinerary_id=item["id"],
                  email_status=email_status, subject_len=len(approved.subject))
        assert updated is not None
        return _to_gql(updated)


schema = strawberry.Schema(query=Query, mutation=Mutation)
