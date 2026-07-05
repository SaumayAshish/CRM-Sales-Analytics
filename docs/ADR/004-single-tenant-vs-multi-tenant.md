# ADR-004: Single-Tenant vs. Multi-Tenant Architecture

**Status:** Accepted
**Date:** 2026-07-05
**Deciders:** Saumay Ashish (BA), Senior Full-Stack Engineer

## Context
The platform models one mid-market B2B SaaS company's internal sales organization. It is built as a portfolio/demonstration project with fixed target metrics (15+ tables, 10,000+ seed records, 4 Power BI dashboards) and a 6-phase delivery plan. A foundational question is whether the schema and RBAC model should support one organization's data (single-tenant) or multiple customer organizations sharing the same deployment with data isolation (multi-tenant), as a real commercial CRM product (like Salesforce or HubSpot itself) would.

## Options Considered
1. **Single-tenant** — the schema and application model exactly one organization. Users, Roles, Leads, Accounts, etc. all belong implicitly to "the company"; no `tenant_id` / `organization_id` partitioning anywhere.
   - Pros: Simpler ERD (no tenant-scoping column on every table, no tenant-aware query filters on every endpoint); every RBAC check is just role + record ownership, not role + record ownership + tenant boundary; matches the fixed target metrics exactly (15+ tables of business data, not business data plus a tenancy layer); faster to reach full feature depth across all 7 modules within the delivery timeline; matches how most internal CRM deployments (and most portfolio CRM builds evaluated by hiring managers) are actually scoped.
   - Cons: Does not demonstrate SaaS multi-tenancy architecture skills directly.
2. **Multi-tenant (shared schema, `tenant_id` on every table)**
   - Pros: More realistic for a CRM *product* (as opposed to a CRM *deployment*); demonstrates SaaS architecture maturity (tenant isolation, per-tenant RBAC, cross-tenant data leakage prevention).
   - Cons: Every table needs a `tenant_id` column and every single query (all 40+ endpoints, all KPI SQL, all RBAC checks) must filter by tenant — this roughly doubles the surface area for bugs (a missed tenant filter is a data leak) and testing effort, directly competing with the 70%+ test coverage target and the fixed delivery timeline. Also complicates seed data generation (10,000+ records now need a plausible multi-org distribution) without adding business-requirement depth to the 7 core modules, which are about sales process depth, not tenancy plumbing.
3. **Multi-tenant via separate schemas or databases per tenant**
   - Pros: Strongest isolation guarantee.
   - Cons: Highest operational complexity (per-tenant migrations, connection routing) for a project with exactly one modeled organization; far outside the scope and timeline of this engagement.

## Decision
**Option 1 — Single-tenant.** The system models one company's sales organization. This decision is revisited only if a future phase explicitly adds multi-org support as a new, separately scoped module (it is not on the 7-module list and would require an updated BRD scope change and a new ADR).

## Consequences
- Every table in `ERD.md` and `Data_Dictionary.md` omits a tenant-scoping column, keeping the schema and RBAC checks focused purely on the role + ownership model described in `Architecture.md` §5.2.
- Seed data (10,000+ records) represents one coherent company's sales history, which makes demo data (dashboards, pipeline views) look like a real company's numbers rather than a thin multi-tenant sample.
- Gap Analysis (`Gap_Analysis.md`) will explicitly note multi-tenancy as a deliberate, out-of-scope gap versus commercial products like Salesforce/HubSpot, framed as a scope decision rather than a limitation the author was unaware of.
- If a future engagement required multi-tenancy, this ADR is the record of why it wasn't built here, and the natural extension point is adding a `tenant_id` column plus tenant-aware middleware — not a rewrite.
