"""FastAPI application: REST health + GraphQL primary API."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from .config import settings
from .logging_setup import log_event
from .schema import schema


def create_app() -> FastAPI:
    app = FastAPI(title="AI Travel Agent API", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log_event("http_request", request_id=request_id, path=request.url.path,
                  method=request.method, status=response.status_code,
                  duration_ms=round((time.perf_counter() - start) * 1000, 2))
        return response

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready():
        # Readiness: process is up; external keys optional (mock mode supported).
        return {"status": "ready", "mock_agent": settings.mock_agent}

    async def graphql_context(request: Request) -> dict:
        return {"request_id": request.headers.get("X-Request-ID", "-")}

    # Strawberry >=0.26 uses schema + context_getter params.
    try:
        graphql_router = GraphQLRouter(schema, context_getter=graphql_context)
    except TypeError:
        graphql_router = GraphQLRouter(schema, context_getter=graphql_context)  # type: ignore

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"error": "bad_request", "detail": str(exc)[:500]})

    # Approval errors surfaced via GraphQL errors; keep REST handler simple.
    app.include_router(graphql_router, prefix="/graphql")
    return app


app = create_app()
