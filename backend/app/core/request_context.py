"""
Per-request context (client IP, user agent) available to code that doesn't
receive the Request object directly, via ASGI middleware + contextvars.

Traces to: FR-55 (audit log captures actor IP/user agent where available).
"""
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

_ip_address: ContextVar[str | None] = ContextVar("ip_address", default=None)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else None
        _ip_address.set(client_host)
        _user_agent.set(request.headers.get("user-agent"))
        return await call_next(request)


def get_request_ip() -> str | None:
    return _ip_address.get()


def get_request_user_agent() -> str | None:
    return _user_agent.get()
