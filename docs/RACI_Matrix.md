# RACI Matrix

**Traceability:** Derived from the Stakeholder Register in `BRD.md` §4. Two matrices are provided: (1) the **in-application RACI** — who does what with system data, day to day, which downstream FRD/RBAC requirements are built from — and (2) the **delivery-governance RACI** — who owns each project artifact/phase.

**Legend:** R = Responsible (does the work) · A = Accountable (owns the outcome, final approver) · C = Consulted (input sought before action) · I = Informed (notified after action)

---

## 1. In-Application RACI (System Activities)

These rows map directly to RBAC enforcement in `Architecture.md` §5.2 and business rules BR-10 through BR-13 in `BRD.md`.

| Activity | Admin | Manager | Rep | Viewer |
|---|---|---|---|---|
| Create a lead | A/R | A/R | R | I |
| Manually assign/reassign a lead | A/R | A/R | I | I |
| Edit own assigned lead/opportunity | A/R | A/R | R | — |
| Edit another rep's lead/opportunity | A/R | A/R (own team only) | — | — |
| Convert lead to Account/Contact/Opportunity | A/R | A/R | R | — |
| Change opportunity pipeline stage | A/R | A/R (own team) | R (own records) | — |
| Reopen a Closed opportunity (BR-17) | A/R | — | — | — |
| Log an activity (call/email/meeting/task) | A/R | A/R | R | — |
| View own team's pipeline dashboard | A/R | A/R | I | I |
| View system-wide pipeline dashboard | A/R | C | — | I |
| Configure lead scoring thresholds (BR-18) | A/R | C | — | — |
| Manage user accounts and role assignment | A/R | I | — | — |
| View audit log | A/R | C (own team scope) | — | — |
| Export/view Power BI dashboards | A/R | A/R | R (own metrics) | R (read-only) |
| Approve forecast roll-up figures | A/R | R | C | I |

---

## 2. Delivery-Governance RACI (Project Artifacts & Phases)

| Phase / Artifact | BA (Saumay Ashish) | Engineering (this assistant) | VP of Sales | Sales Ops Manager | Regional Managers | IT/Security Lead |
|---|---|---|---|---|---|---|
| BRD | A/R | C | A (final sign-off) | C | I | I |
| FRD | A/R | C | I | A (functional sign-off) | C | C |
| ERD / Data Dictionary | R | A/R (technical accuracy) | I | C | I | C |
| Architecture / ADRs | C | A/R | I | I | I | C |
| KPI Catalog | A/R | C | C | A (business validation) | C | I |
| User Stories | A/R | C | I | C | C | — |
| UAT Test Scripts | A/R | C | I | A (UAT sign-off) | R (executes cases) | C |
| RBAC / Audit Log implementation | C | A/R | I | I | I | A (compliance sign-off) |
| Phase 1 Completion Report | A/R | C | I | I | I | — |
| Go-live decision | C | C | A | R | C | C |

---

## 3. Notes on Interpretation

- **Manager scope is always team-bounded.** A Regional Sales Manager is Accountable/Responsible only for their own team's records — not system-wide — consistent with BR-11.
- **Viewer is never Responsible for a write action.** The Viewer row in §1 contains no R against any create/update/delete activity, consistent with BR-12.
- **Admin is Accountable for every in-application row** because Admin has system-wide reach by design (§5.2 of `Architecture.md`), but day-to-day Responsible work is expected to sit with Manager/Rep — Admin involvement in routine lead/opportunity edits is an exception path, not the norm.
- **Dual A/R cells** (e.g., Admin and Manager both marked A/R on "Create a lead") reflect that either role can independently perform and own that action; this is intentional and should not be read as ambiguity — the RBAC model (see `Architecture.md`) permits both, with Rep as the primary expected actor for day-to-day lead creation.
