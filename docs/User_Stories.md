# User Stories

**Traceability:** `US-xx` decomposes `FR-xx` (`FRD.md`) into implementable, testable increments. Each story traces forward to at least one `UAT-xx` case in `UAT_Test_Scripts.md`.
**Format:** As a [role], I want [action], so that [benefit]. Acceptance criteria in Given/When/Then. Estimate: Fibonacci (1,2,3,5,8). Priority: MoSCoW (Must/Should/Could/Won't).

**Total stories: 42** across 7 Epics (one per module).

---

## Epic 1: Lead Management

### Feature 1.1 — Lead Capture

**US-01** | Traces: FR-01 | Points: 3 | Priority: Must
As a Sales Rep, I want to create a new lead with core contact and source details, so that no inbound interest is lost.
- Given I am logged in as a Rep, When I submit a lead form missing the email field, Then the system rejects the submission with a field-level validation error.
- Given valid required fields, When I submit the form, Then a new lead record is created with `created_at` set to the current time.

**US-02** | Traces: FR-01 | Points: 2 | Priority: Should
As a Sales Ops Manager, I want lead source to be selected from a standardized list, so that source reporting (KPI Catalog) stays consistent.
- Given the lead form, When I open the source dropdown, Then only values from `lead_sources` are selectable (no free text).

### Feature 1.2 — Lead Scoring & Assignment

**US-03** | Traces: FR-02, FR-03 | Points: 5 | Priority: Must
As a system, I want to automatically score a lead at creation, so that Reps can prioritize follow-up without manual triage.
- Given a new lead is created, When the save transaction completes, Then the lead has a non-null `score` and `score_band`.

**US-04** | Traces: FR-04 | Points: 5 | Priority: Must
As a Sales Ops Manager, I want Hot leads to auto-assign to a Rep immediately, so that response time drops from days to minutes (OBJ-02).
- Given a lead's score crosses the Hot threshold, When scoring completes, Then `assigned_to` is populated within the same processing cycle.

**US-05** | Traces: FR-05 | Points: 3 | Priority: Must
As a Manager, I want to manually reassign any lead in my team, so that I can rebalance workload.
- Given I am a Manager, When I reassign a lead to another Rep on my team, Then the change persists and an audit entry is written.
- Given I am a Rep, When I attempt to reassign a lead, Then the API returns 403.

**US-06** | Traces: FR-08 | Points: 2 | Priority: Should
As a Manager, I want to see all unassigned leads in one queue, so that none go stale.
- Given leads exist with `assigned_to = NULL`, When I open the unassigned queue, Then all such leads appear, sorted by creation date ascending.

### Feature 1.3 — Lead Conversion

**US-07** | Traces: FR-06 | Points: 8 | Priority: Must
As a Rep, I want to convert a qualified lead into an Account, Contact, and Opportunity in one action, so that I don't re-enter the same data three times.
- Given a qualified, unconverted lead, When I click "Convert," Then an Account, a Contact, and an Opportunity are created atomically and the lead is flagged `is_converted = true`.

**US-08** | Traces: FR-07 | Points: 2 | Priority: Must
As a system, I want to block re-conversion of an already-converted lead, so that duplicate Accounts aren't created.
- Given a lead with `is_converted = true`, When a conversion is attempted again, Then the API returns 409.

---

## Epic 2: Opportunity Pipeline (Kanban)

### Feature 2.1 — Pipeline Visualization

**US-09** | Traces: FR-10 | Points: 5 | Priority: Must
As a Rep, I want to see my opportunities on a Kanban board grouped by stage, so that I can visually track my deal progress.
- Given I have opportunities in multiple stages, When I open the pipeline view, Then each stage renders as a column with correct opportunity counts and total value.

**US-10** | Traces: FR-16 | Points: 3 | Priority: Should
As a Manager, I want to filter the Kanban board by owner and date range, so that I can review a specific rep's or period's pipeline.
- Given filters are applied, When the board reloads, Then only matching opportunities display, fetched via server-side filtering.

### Feature 2.2 — Stage Management

**US-11** | Traces: FR-11 | Points: 5 | Priority: Must
As a Rep, I want to move an opportunity to the next stage via drag-and-drop, so that pipeline status stays current without extra clicks.
- Given I drag a card to a new column, When the drop completes, Then the API persists the new `stage_id` and an audit entry is created.

**US-12** | Traces: FR-09 | Points: 2 | Priority: Must
As a system, I want to reject invalid stage values, so that the pipeline never enters an undefined state.
- Given a stage-change request with a value not in the `pipeline_stages` enum, When submitted, Then the API returns 422.

**US-13** | Traces: FR-12 | Points: 3 | Priority: Must
As a Rep, I want to be required to enter a loss reason when marking a deal Closed Lost, so that leadership can analyze loss patterns (KPI Catalog).
- Given I set stage to Closed Lost without a `loss_reason_id`, When I submit, Then the API returns 422.

**US-14** | Traces: FR-14 | Points: 3 | Priority: Should
As an Admin, I want to reopen a closed opportunity with a documented reason, so that genuine data-entry errors can be corrected without bypassing governance.
- Given a Closed opportunity, When an Admin changes its stage with a reason, Then the change succeeds and is audit-logged; the same action by a Manager/Rep returns 403.

### Feature 2.3 — Forecasting Support

**US-15** | Traces: FR-15 | Points: 3 | Priority: Must
As a Manager, I want to see weighted pipeline value per opportunity and in aggregate, so that I can build a realistic forecast (OBJ-04).
- Given an opportunity with amount and probability set, When I view it, Then weighted value = amount × probability is displayed and recalculates on change.

**US-16** | Traces: FR-13 | Points: 2 | Priority: Must
As a system, I want every opportunity to require exactly one account and one owner, so that pipeline reporting never has orphaned deals.
- Given a create-opportunity request missing `account_id`, When submitted, Then the API returns 422.

---

## Epic 3: Account & Contact 360

### Feature 3.1 — Unified Account View

**US-17** | Traces: FR-17 | Points: 5 | Priority: Must
As a Rep, I want a single Account page showing contacts, opportunities, and activities, so that I have full context before a customer call.
- Given an account with related records, When I open the Account 360 view, Then all four related record types display without requiring separate navigation.

**US-18** | Traces: FR-22 | Points: 3 | Priority: Should
As a Manager, I want to search accounts by name, region, or owner, so that I can quickly locate a specific customer.
- Given a search term, When I search, Then matching accounts return server-side, paginated.

### Feature 3.2 — Contact Management

**US-19** | Traces: FR-18 | Points: 3 | Priority: Must
As a Rep, I want to designate one contact as primary per account, so that outreach defaults to the right person.
- Given an account with an existing primary contact, When I mark a different contact primary, Then the previous primary is automatically un-flagged in the same transaction.

**US-20** | Traces: FR-19 | Points: 3 | Priority: Should
As a Rep, I want to be warned when creating an account that looks like a duplicate, so that we avoid fragmented customer records.
- Given an account name/domain matches an existing account, When I attempt to save, Then a warning displays and requires an explicit override reason to proceed.

### Feature 3.3 — Extensibility & History

**US-21** | Traces: FR-20 | Points: 3 | Priority: Could
As an Admin, I want to store custom fields on leads/accounts without a schema migration, so that Sales Ops can adapt to new data needs quickly.
- Given a custom field key-value pair, When saved via API, Then it round-trips correctly on the next GET request.

**US-22** | Traces: FR-21 | Points: 2 | Priority: Should
As a Manager, I want to view an account's full edit history, so that I can understand how a deal's terms evolved.
- Given prior changes exist, When I open the history tab, Then entries display sourced from `audit_logs`, most recent first.

---

## Epic 4: Activity Tracking

### Feature 4.1 — Logging Activities

**US-23** | Traces: FR-23 | Points: 3 | Priority: Must
As a Rep, I want to log a call, email, meeting, or task against a lead/account/contact/opportunity, so that my interaction history is never lost to personal notes.
- Given no related entity is selected, When I try to save an activity, Then the API rejects it with 422.

**US-24** | Traces: FR-24 | Points: 3 | Priority: Should
As a Rep, I want type-specific fields (call duration, meeting attendees, task due date), so that the activity record captures relevant detail.
- Given I select "Task" as the type, When the form renders, Then a due-date field is required and a call-duration field is hidden.

### Feature 4.2 — Timeline & Tasks

**US-25** | Traces: FR-25 | Points: 3 | Priority: Must
As a Rep, I want a chronological activity timeline on each account/opportunity, so that I can quickly catch up on history.
- Given multiple activities exist, When I view the timeline, Then entries display newest-first and paginate beyond the page-size limit.

**US-26** | Traces: FR-26 | Points: 2 | Priority: Should
As a Rep, I want overdue tasks flagged visually, so that nothing slips through the cracks.
- Given a task with `due_at` in the past and `is_complete = false`, When I view my task list, Then it displays with an overdue indicator.

**US-27** | Traces: FR-27 | Points: 2 | Priority: Must
As a system, I want to restrict activity logging to records a Rep owns, so that data ownership boundaries (BR-11) hold across all modules.
- Given a Rep attempts to log an activity against another rep's opportunity, When submitted, Then the API returns 403.

---

## Epic 5: Sales Analytics Dashboards

### Feature 5.1 — Dashboard Delivery

**US-28** | Traces: FR-28 | Points: 5 | Priority: Must
As a VP of Sales, I want a Pipeline Health dashboard, so that I can see total pipeline value and stage distribution without a status meeting.
- Given seeded pipeline data, When the dashboard loads, Then it reflects current stage totals matching a direct SQL query against the same data.

**US-29** | Traces: FR-28 | Points: 5 | Priority: Must
As a Sales Ops Manager, I want a Lead Performance dashboard, so that I can see conversion rates by source and score band.
- Given seeded lead data, When the dashboard loads, Then conversion-rate figures match the KPI Catalog formula computed independently.

**US-30** | Traces: FR-28 | Points: 5 | Priority: Must
As a Regional Manager, I want a Rep Performance dashboard, so that I can review quota attainment and activity volume per rep on my team.
- Given team-scoped access, When I open the dashboard, Then only my team's reps display (not other regions').

**US-31** | Traces: FR-28 | Points: 5 | Priority: Must
As a VP of Sales, I want a Forecast Accuracy dashboard, so that I can track forecast-vs-actual variance over time (OBJ-04).
- Given closed opportunities across multiple quarters, When the dashboard loads, Then variance is computed per quarter per the KPI Catalog formula.

### Feature 5.2 — Governance & Access

**US-32** | Traces: FR-30 | Points: 3 | Priority: Must
As a Rep, I want to see only my own performance metrics on the Rep Performance dashboard, so that peer performance data isn't exposed to me.
- Given I am logged in as a Rep, When I open the dashboard, Then only my own row/metrics render.

**US-33** | Traces: FR-32 | Points: 3 | Priority: Could
As a Manager, I want to drill through from a KPI tile to the underlying records, so that I can investigate an anomaly without leaving the dashboard.
- Given a summary tile showing "12 Hot Leads," When I click it, Then the 12 underlying lead records display in a list.

---

## Epic 6: Workflow Automation

### Feature 6.1 — Scoring Configuration

**US-34** | Traces: FR-33, FR-34 | Points: 5 | Priority: Must
As an Admin, I want to configure lead scoring criteria and weights, so that the model reflects current sales priorities without a code deployment.
- Given I update a scoring criterion's weight via the config API, When a new lead is scored, Then the new weight applies without a code change.

**US-35** | Traces: FR-37 | Points: 2 | Priority: Should
As an Admin, I want to disable a scoring or assignment rule without deleting it, so that I can pause automation temporarily and re-enable later.
- Given a rule marked `is_active = false`, When the scoring/assignment cycle runs, Then that rule is skipped but remains in configuration.

### Feature 6.2 — Assignment Logic

**US-36** | Traces: FR-35 | Points: 5 | Priority: Must
As a Sales Ops Manager, I want lead auto-assignment to follow a documented, reproducible strategy, so that reps trust the fairness of lead distribution (RISK-02).
- Given identical input leads and an unchanged rep roster, When assignment runs twice, Then the outcome is identical both times.

**US-37** | Traces: FR-36 | Points: 2 | Priority: Must
As an Admin, I want automated actions logged distinctly from manual actions, so that I can distinguish system behavior from human behavior in the audit log.
- Given an auto-assignment event, When I inspect the audit log, Then `actor_id` is null or a system identifier, not a human user ID.

---

## Epic 7: RBAC + Audit Log

### Feature 7.1 — Authentication & Roles

**US-38** | Traces: FR-38 | Points: 5 | Priority: Must
As a User, I want to log in and receive a role-bearing token, so that the system knows what I'm allowed to do.
- Given valid credentials, When I log in, Then I receive a JWT containing my role claim, and an expired token is rejected on subsequent requests.

**US-39** | Traces: FR-42 | Points: 3 | Priority: Must
As an Admin, I want to create and deactivate user accounts, so that offboarded employees immediately lose access.
- Given a deactivated user, When they attempt to log in, Then authentication fails regardless of correct password.

### Feature 7.2 — Access Enforcement

**US-40** | Traces: FR-39 | Points: 5 | Priority: Must
As a system, I want every protected endpoint to enforce role boundaries server-side, so that RBAC cannot be bypassed by calling the API directly.
- Given a Viewer calls a lead-creation endpoint directly (bypassing the UI), When the request is processed, Then it returns 403.

### Feature 7.3 — Audit Trail

**US-41** | Traces: FR-40 | Points: 5 | Priority: Must
As an IT/Security Lead, I want every mutation on core entities logged immutably, so that any data change can be reconstructed after the fact (OBJ-05).
- Given any create/update/delete on a Lead/Account/Contact/Opportunity/User, When the operation completes, Then exactly one new audit_logs row exists for it.

**US-42** | Traces: FR-41 | Points: 2 | Priority: Must
As an IT/Security Lead, I want the audit log to be immutable even to Admins through the application, so that the accountability record can't be tampered with after the fact.
- Given an Admin attempts a PATCH/DELETE on an audit log entry via the API, When the request is sent, Then no such route exists (405/404).

---

## Epic 8: Backend Advanced (Phase 3)

Added 2026-07-05 to cover FR-46–FR-64, per FRD.md §10's traceability note.

### Feature 8.1 — Pipeline Stage Engine

**US-43** | Traces: FR-46, FR-47 | Points: 5 | Priority: Must
As an Admin, I want to configure which stages a deal can move to next, so that the funnel reflects our actual sales process without a code change.
- Given Qualification's allowed next-stages are Needs Analysis and Closed Lost, When a Rep tries to advance directly to Negotiation, Then the API returns 422 unless a Manager/Admin supplies an override reason.

**US-44** | Traces: FR-48 | Points: 2 | Priority: Should
As a Manager, I want to see an opportunity's full stage history, so that I can understand how a deal progressed without asking the rep.
- Given an opportunity has changed stage three times, When I view its stage history, Then all three transitions display chronologically with actor and timestamp.

### Feature 8.2 — Lead Scoring Engine

**US-45** | Traces: FR-49, FR-52 | Points: 5 | Priority: Must
As a system, I want to re-run scoring whenever a lead is created, updated, or gets a new activity, so that the score always reflects current information.
- Given a lead crosses into Hot after a new activity is logged, When scoring completes, Then the lead is auto-assigned to the least-loaded active Rep.

**US-46** | Traces: FR-51 | Points: 3 | Priority: Should
As a Rep, I want to see exactly which criteria contributed to a lead's score, so that I trust the scoring model isn't a black box.
- Given a lead scored 45 from two matched criteria, When I view its score breakdown, Then both criteria and their weights are listed and sum to 45.

### Feature 8.3 — Workflow Automation & Notifications

**US-47** | Traces: FR-58, FR-59 | Points: 5 | Priority: Must
As an Admin, I want to define a rule that fires on a named event only when conditions match, so that automation stays predictable and auditable.
- Given a rule targets `lead_scored` with condition `score_band equals Hot`, When a Warm lead is scored, Then the rule evaluates but does not match, and no action executes.

**US-48** | Traces: FR-60, BR-22 | Points: 3 | Priority: Should
As a Manager, I want to be notified in-app when a lead goes Hot, so that I don't have to poll dashboards to catch it.
- Given a matching `send_notification` action runs, When I check my notifications, Then the new notification appears unread.

**US-49** | Traces: FR-61 | Points: 2 | Priority: Should
As an Admin, I want to see why a rule did or didn't fire, so that I can debug unexpected automation behavior.
- Given a rule's conditions didn't match on the last three events, When I view its execution log, Then all three appear with `matched=false`.

### Feature 8.4 — Audit & Analytics

**US-50** | Traces: FR-56 | Points: 2 | Priority: Must
As an IT/Security Lead, I want the database itself to reject any attempt to alter audit history, so that the guarantee holds even if the application layer is bypassed.
- Given a direct SQL UPDATE against `audit_logs`, When executed, Then Postgres rejects it via the immutability trigger, independent of the API.

**US-51** | Traces: FR-57 | Points: 3 | Priority: Should
As a Manager, I want to query the audit log scoped to my own team, so that I can review my team's activity without seeing other regions'.
- Given entries exist from actors on two different teams, When a Manager queries the audit log, Then only their own team's entries return.

**US-52** | Traces: FR-64 | Points: 3 | Priority: Must
As a VP of Sales, I want pipeline, rep-performance, funnel, and forecast figures available via API, so that Power BI dashboards (Phase 5) can consume live data.
- Given seeded pipeline data, When I call `/analytics/pipeline-summary`, Then the returned totals match an independently-run SQL query against the same tables.

---

## Summary Statistics

- **Total stories:** 52 (exceeds the 40+ target)
- **By priority:** Must = 33, Should = 15, Could = 4, Won't = 0 (all in-scope stories are at least Could — no story is currently deprioritized to Won't; any future Won't-priority ask should be logged against `Gap_Analysis.md` instead)
- **Total story points:** 178 (indicative sizing only — not a sprint-commitment forecast)
