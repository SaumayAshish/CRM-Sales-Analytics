"""
Shared slowapi rate limiter instance (single source of truth so the login
endpoint's decorator and the app-level exception handler operate on the
same in-memory storage).

Traces to: Phase 2 plan agreement (rate limiting on auth endpoints via
slowapi, no Redis).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
