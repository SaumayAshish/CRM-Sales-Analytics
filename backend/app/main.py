"""
FastAPI application entrypoint.

Traces to: Architecture.md SS3 (OpenAPI auto-docs at /docs and /redoc),
FRD.md SS5.2 (REST/JSON API surface, consistent error responses).
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.routers import (
    accounts,
    activities,
    auth,
    contacts,
    leads,
    lookups,
    opportunities,
    users,
)
from app.core.limiter import limiter
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="CRM & Sales Analytics Platform API",
    description="Backend REST API for the CRM & Sales Analytics Platform. "
    "See docs/FRD.md for the full functional requirement traceability.",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error_code": "internal_server_error", "message": "An unexpected error occurred."},
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(activities.router, prefix="/api/v1/activities", tags=["activities"])
app.include_router(lookups.router, prefix="/api/v1/lookups", tags=["lookups"])
