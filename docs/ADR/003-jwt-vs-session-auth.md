# ADR-003: JWT vs. Server-Side Session Authentication

**Status:** Accepted
**Date:** 2026-07-05
**Deciders:** Saumay Ashish (BA), Senior Full-Stack Engineer

## Context
The platform needs an authentication mechanism that supports 4 fixed roles (Admin, Manager, Rep, Viewer) enforced on every API call, works cleanly with a containerized deployment (Docker Compose, no shared session store configured by default), and is straightforward to demo/test (login, call protected endpoints, show RBAC denial).

## Options Considered
1. **JWT (stateless) bearer tokens**
   - Pros: No server-side session store required — fits a simple Docker Compose deployment without adding Redis or a sticky-session layer (Redis is explicitly excluded per CLAUDE.md unless justified); the token itself carries role claims, so RBAC checks are a fast in-memory decode rather than a DB/cache lookup on every request; standard, well-understood pattern for REST APIs and easy to demonstrate/test with tools like Postman/pytest.
   - Cons: Revocation before expiry is harder (mitigated with short-lived access tokens + refresh token rotation); token size slightly larger than a session ID.
2. **Server-side sessions (session ID in cookie, session state in a store)**
   - Pros: Instant revocation (delete the session server-side); smaller cookie payload.
   - Cons: Requires a shared session store for the session data. In a single-instance Docker Compose deployment this could live in Postgres, but that adds write load to the primary database for every request's session touch, or it pushes toward Redis — explicitly excluded from the stack unless justified in writing, and not justified here given the project's scale (single organization, mid-market, not multi-instance horizontally scaled).
3. **JWT with a Postgres-backed revocation/denylist table**
   - Pros: Combines stateless verification with the ability to revoke specific tokens (e.g., on logout or admin-forced deactivation).
   - Cons: Adds a DB check on every request, partially negating the "no lookup" benefit of pure JWT, though the check is a simple indexed lookup, not a full session hydration.

## Decision
**Option 3 — JWT access tokens (short-lived, ~15 min) with refresh token rotation, plus a lightweight Postgres `revoked_tokens` table checked only on refresh (not on every access-token request).** This keeps most requests stateless and fast while still allowing an Admin to force-revoke a user's session (e.g., on deactivation) without needing Redis.

## Consequences
- RBAC claims (role, user ID) are embedded in the access token, so every protected endpoint can authorize in-process without an extra database round-trip for the common case.
- Logout / forced deactivation works by revoking the refresh token, which is checked only when a new access token is requested (low-frequency operation), keeping the hot path fast.
- No Redis or additional infrastructure is introduced, keeping the stack aligned with CLAUDE.md's locked technology list.
- Trade-off accepted: an access token cannot be instantly invalidated mid-lifetime (up to ~15 minutes of validity even after revocation is requested) — acceptable for this system's risk profile (internal sales tool, not a financial transaction system) and documented here so it isn't mistaken for an oversight.
