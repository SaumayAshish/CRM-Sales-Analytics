# Process Flow: Opportunity-to-Close (Deal Progression)

**Traces to:** BR-05 through BR-07, BR-16, BR-17, FR-09 through FR-16

## Swimlane Diagram

```mermaid
flowchart TD
    subgraph LaneRep["Sales Rep"]
        A["Opportunity created at lead conversion (stage = Qualification)"]
        B[Rep advances deal through Needs Analysis]
        C[Rep sends Proposal]
        D[Rep enters Negotiation]
        E{Deal outcome?}
        F["Rep marks Closed Won"]
        G["Rep marks Closed Lost + selects loss_reason (BR-07)"]
    end

    subgraph LaneSystem["System (Automated)"]
        S1["Validate stage transition against fixed enum (FR-09)"]
        S2["Recalculate weighted value = amount x probability (FR-15)"]
        S3["Write audit log entry per stage change (BR-14)"]
        S4{"loss_reason present?"}
        S5["Reject: 422 (FR-12)"]
        S6["Set closed_at timestamp, lock stage (BR-17)"]
    end

    subgraph LaneAdmin["Admin (Exception Path Only)"]
        X["Admin reopens Closed opportunity with documented reason"]
    end

    A --> B --> S1 --> S2 --> S3
    B --> C --> S1
    C --> D --> S1
    D --> E
    E -->|Won| F --> S1
    E -->|Lost| G --> S1 --> S4
    S4 -->|No| S5
    S4 -->|Yes| S6
    F --> S6
    S6 --> Y[Opportunity locked; reflected in Forecast Accuracy dashboard]
    Y -.->|Admin override only, BR-17| X --> S1
```

## Decision Gates

| Gate | Condition | Path |
|---|---|---|
| Stage transition validity | Is the target stage a valid enum value in the fixed sequence? | Valid → proceed; Invalid → 422 rejection (FR-09) |
| Closed Lost completeness | Is `loss_reason_id` populated? | Yes → finalize as Closed Lost; No → reject save (FR-12) |
| Post-close mutation | Is the actor an Admin providing a reason? | Yes → reopen permitted, logged; No (Manager/Rep) → 403 (BR-17, FR-14) |

## Exception Paths

| Exception | Handling |
|---|---|
| Rep attempts to skip a stage (e.g., Qualification → Negotiation directly) | Allowed by default (stage order is informational for the Kanban view, not a hard sequential gate) unless Sales Ops configures strict sequential enforcement — documented here as a configuration choice, not a hardcoded restriction, since real sales cycles don't always move linearly. |
| Two users change the same opportunity's stage simultaneously | Last write wins at the DB transaction level; both attempts are individually audit-logged so the sequence is reconstructable (see `FRD.md` §8). |
| Closed opportunity needs correction after go-live | Only Admin can reopen, must supply a reason, and the action is fully audited (BR-17, FR-14). |
