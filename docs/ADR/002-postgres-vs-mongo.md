# ADR-002: PostgreSQL vs. MongoDB

**Status:** Accepted
**Date:** 2026-07-05
**Deciders:** Saumay Ashish (BA), Senior Full-Stack Engineer

## Context
The core domain (Leads, Accounts, Contacts, Opportunities, Activities, Users, Roles, Audit Logs) is highly relational: an Opportunity belongs to an Account, an Account has many Contacts, a Lead converts into an Account/Contact/Opportunity triplet, and Activities reference multiple entity types. The platform also needs to support 20+ KPIs computed via SQL and consumed by Power BI, and an audit log with strict integrity guarantees (who did what, when, to which record).

## Options Considered
1. **PostgreSQL 16 (relational)**
   - Pros: Native foreign key constraints enforce referential integrity (an Opportunity cannot reference a non-existent Account); mature window function and CTE support makes KPI SQL (pipeline velocity, conversion rates, cohort analysis) straightforward; Power BI has first-class native connectors for Postgres; ACID transactions guarantee audit log correctness even under concurrent writes; free, well-documented, industry-standard for CRM-style OLTP workloads.
   - Cons: Schema changes require migrations (less flexible for rapidly changing document shapes — not a concern here since the CRM schema is well-understood domain).
2. **MongoDB (document)**
   - Pros: Schema flexibility, natural fit if data shapes were highly variable or nested documents were the dominant access pattern.
   - Cons: No native foreign key enforcement — referential integrity between Leads/Accounts/Opportunities would need to be enforced entirely in application code, which is a correctness risk for a CRM where "an opportunity references a real account" is a hard business rule, not a nice-to-have. Aggregation pipeline syntax for KPI-style reporting is more verbose and less familiar to the target audience (BI/analytics teams expect SQL). Power BI's Mongo connector is less mature than its Postgres connector.
3. **Hybrid (Postgres + Mongo for activity logs / unstructured notes)**
   - Pros: Could use Mongo for free-text activity notes or flexible custom fields.
   - Cons: Two datastores to operate, back up, and secure for marginal benefit; directly increases operational complexity the project is trying to avoid (see ADR-001); Postgres `JSONB` columns already provide semi-structured flexibility where genuinely needed (e.g., custom field storage) without a second database.

## Decision
**PostgreSQL 16**, using `JSONB` columns only where genuine schema flexibility is needed (e.g., a `custom_fields` column on Lead/Account for future extensibility), while all core relationships remain strictly relational with foreign keys and constraints.

## Consequences
- Referential integrity (an Opportunity must belong to a real Account; a Contact must belong to a real Account) is enforced at the database level, not just application code — reduces a whole class of data-corruption bugs.
- KPI SQL (in `KPI_Catalog.md`) can be written and tested directly against the schema, and handed to Power BI with minimal transformation.
- Audit log writes benefit from transactional guarantees — an entity update and its audit record either both commit or neither does.
- Trade-off accepted: less flexibility for arbitrary schema-less data; mitigated by selective `JSONB` usage where the business genuinely needs it (documented per-table in `Data_Dictionary.md`).
