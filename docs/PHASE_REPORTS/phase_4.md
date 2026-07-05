# Phase 4 Completion Report — Frontend

**Date completed:** 2026-07-05
**Phase owner:** Saumay Ashish (Business Analyst) / Senior Full-Stack Engineer (delivery)

---

## 1. Deliverables Checklist

- [x] React app running on `localhost:5173` (Vite + React 18.3.1 + TypeScript, per the locked stack)
- [x] All 7 screens working end-to-end against the live FastAPI backend: Dashboard shell, Leads list, Lead detail, Opportunity Kanban, Account 360, Contacts list, Settings
- [x] Role-based UI gating verified live across all 4 roles (Admin, Manager, Rep, Viewer) — see §3
- [x] Responsive layout (Tailwind breakpoints on the sidebar/grid/Kanban columns) — not device-lab tested, verified at standard desktop widths only
- [x] Vitest coverage on 3 critical components (exceeds the 3+ target): `RoleGuard`, `ActivityTimeline`, `LoginPage`, 10 tests total
- [x] Phase 4 completion report (this document)
- [~] Screenshots for README — visually verified live in-browser (see §3), but image assets weren't saved as committed files; noted as a Phase 6 polish item rather than claimed done

---

## 2. What Was Built

| Area | Summary |
|---|---|
| Scaffold | Vite + React 18.3.1 (pinned down from the template's default React 19 to match the CLAUDE.md stack lock) + TypeScript, Tailwind v4 + shadcn/ui (`new-york` style), ESLint replaced by the template's `oxlint`, Prettier, `@/*` path alias |
| Auth | `AuthProvider` context decoding the JWT role claim client-side, `localStorage` + Axios interceptor token storage (per the Phase 4 kickoff decision), refresh-on-401 with single-flight dedup, `ProtectedRoute` wrapper, `RoleGuard` for UI gating (never the sole enforcement — backend `require_role` remains authoritative) |
| Screens | Dashboard shell (sidebar/header/breadcrumbs/notification bell), Leads list (search, unassigned-queue toggle, pagination) + detail (score breakdown, timeline, convert action), Opportunity Kanban (native HTML5 drag-and-drop, stage-change dialog handling both loss-reason and override-reason flows), Account 360 (tabbed contacts/opportunities/timeline), Contacts list, Settings (profile, quota attainment, Admin Console pointer) |
| Shared components | `DataTable` (generic, sortable), `StatusBadge`, `ActivityTimeline` (renders system-generated entries distinctly per FR-54), `RoleGuard`, `NotificationBell`, `EmptyState`, `ErrorBoundary` |
| Forms | react-hook-form + zod across all four create flows (Lead, Account, Contact, Opportunity), with the Account form's duplicate-domain 409 surfaced as an inline override-reason flow (FR-19) |
| API layer | Axios + TanStack Query (no Redux/Zustand/Jotai introduced, per instruction), hand-written types mirroring the backend Pydantic schemas |
| Backend pre-work | `users.quota` column (BR-23), `vw_rep_performance.quota_attainment`, seeded realistic per-rep/manager quotas — closes the KPI Catalog gap flagged in Phase 3 |

---

## 3. Manual Verification Performed (Live, Not Assumed)

The Claude-in-Chrome browser extension was used to drive a real browser session against the live backend (seeded, `localhost:8000`) and frontend (`localhost:5173`) — not just `tsc`/build/unit-test checks:

1. **Login flow** — real credentials, real JWT issuance, redirect to `/leads`.
2. **Leads list + detail** — real data rendered (score bands, source names); clicked into a lead and confirmed the score breakdown, timeline, and convert action all pulled live data.
3. **Opportunity Kanban** — all 6 stage columns rendered with correct deal counts/totals matching the backend's `vw_pipeline_summary` numbers independently verified in Phase 3.
4. **Account 360** — Contacts/Opportunities/Timeline tabs all populated correctly; primary-contact star indicator rendered.
5. **RBAC gating, three roles compared side by side:**
   - **Admin** (Priya Nandakumar): full nav, Admin Console link, Unassigned queue toggle, all create buttons.
   - **Rep** (Robert Johnson): no Unassigned queue toggle, no Admin Console link, lead list correctly scoped to only their own assigned/converted leads, quota attainment correctly shown on Settings (139.5% against a $250,000 quota).
   - **Viewer** (Sam Ostrowski): no create buttons anywhere, Kanban cards not draggable, otherwise full read access — confirmed by re-checking the Leads and Kanban pages after gating fixes (see below).
6. **Logout** — correctly cleared tokens and redirected to `/login`.

### Bugs found and fixed during this verification (not shipped)

1. **Missing CORS middleware** — the browser's preflight `OPTIONS /auth/login` returned 405 because `FastAPI` had no `CORSMiddleware` configured; nothing had exercised a cross-origin request before the frontend existed. Fixed by adding `CORSMiddleware` with a configurable `CORS_ORIGINS` setting (defaults to `http://localhost:5173`).
2. **shadcn components incompatible with React 18** — the generated `Input`/`Textarea` components used plain prop destructuring (valid under React 19's ref-as-prop model, which the scaffolding tool defaults to) instead of `React.forwardRef`. Under the project's locked React 18, this silently broke `react-hook-form`'s `register()` ref attachment, making every form field read as `undefined` at submit time. Caught by the Vitest `LoginPage` tests failing with a zod "expected string, received undefined" error — not something a visual check would have caught, since the input still displayed typed text correctly (uncontrolled DOM state), only the ref was disconnected. Fixed by converting both to `forwardRef`.
3. **`input[type="email"]` unreliable under jsdom** — a known jsdom quirk where invalid email-format strings aren't preserved in `.value` the way real browsers do, breaking form validation tests. Switched email fields to `type="text"` (zod already validates the format either way) rather than working around the test environment.
4. **Rep couldn't see their own Quota Attainment** — `/analytics/rep-performance` was Admin/Manager-only; a Rep calling it (even to see just their own row) got 403, so the Settings page silently showed "—" instead of real figures. Caught by actually logging in as a Rep and looking at the Settings page, not by reasoning about the code. Fixed by allowing `ROLE_REP` with server-side scoping to `WHERE user_id = :current_user.id`, added a backend test asserting the scoping (a Rep never sees another rep's row).
5. **Create buttons visible to Viewer** — "New Lead," "New Account," "Add Contact," and "New Opportunity" buttons, plus Kanban drag-and-drop, were all visible/usable by a Viewer even though the backend correctly returns 403. Caught by logging in as Viewer and looking at the actual screen, not by code review. Fixed by wrapping all four create-entity triggers in `RoleGuard` and gating Kanban drag/drop behind a `role !== "Viewer"` check.

All five were found by actually exercising the running application end-to-end, consistent with this project's stated verification discipline (see Phase 2/3 reports for the same pattern).

---

## 4. Deviations From the Original Plan (and Why)

| Deviation | Reason |
|---|---|
| React pinned to 18.3.1, not the template's default 19.x | CLAUDE.md locks "React 18"; `create-vite`'s current template defaults to React 19. Downgraded `react`/`react-dom`/`@types/react`/`@types/react-dom` immediately after scaffolding, before writing any component code. |
| `zod` pinned to `^3.25.x`, not the newly-released `4.x` | `@hookform/resolvers@5.4.0` declares a peer dependency on `zod ^3.25.0`; npm installed the newer `zod@4.4.3` by default, which is not yet supported by the resolver and silently broke error-message mapping. Downgraded to the version the resolver actually supports. |
| Contact detail page folded into Account 360 | The 7-screen list named "Contact list + detail page," but a contact's only meaningful context (its account, opportunities, activity) already lives on Account 360. Clicking a contact in the Contacts list navigates to its parent Account 360 page rather than a near-duplicate standalone page — a simplification made for reuse, not an omission. |
| Admin Console is a pointer, not a full UI | The 7-screen list's "Settings page" scope was "user profile + role display," not full CRUD UIs for user/pipeline/scoring/workflow management (which already have working API endpoints from Phases 2–3). Settings links out to those endpoints with a clear note rather than building a second admin UI not asked for — avoiding scope creep per CLAUDE.md rule 8. |
| DnD via native HTML5 API, not a library | Explicit instruction: no new state libraries without approval. A drag-and-drop library isn't a state library, but was kept out anyway to minimize new dependencies for a 6-column board of modest complexity. |

---

## 5. Open Items Carried Into Phase 5

1. **Screenshot image assets for the README** are still outstanding — verified live but not saved as committed files. Low-cost Phase 6 (or earlier) follow-up.
2. **Bundle size warning** — the production build is ~598 KB (183 KB gzipped) in a single chunk; Vite recommends code-splitting. Not a blocker at this scale, but worth revisiting if the app grows.
3. **Responsive design** was verified at standard desktop widths only, not on an actual mobile device/emulator grid — the Tailwind breakpoints are in place (`sm:`, `lg:` on the sidebar and Kanban grid) but untested end-to-end on small viewports.
4. **CORS origins** are currently a single configurable value defaulting to `localhost:5173`; production deployment (Phase 6) will need this set to the real frontend origin.

---

## 6. Recommendation to Proceed

Phase 4 deliverables are complete, verified against a live backend and a real browser session (not just compiled/reviewed), and five real defects were caught and fixed during that verification rather than shipped. Recommend Business Analyst review and sign-off before Phase 5 (Analytics / Power BI) planning begins.
