// Traces to: FR-25, FR-53 (chronological timeline), FR-54 (system-generated
// entries render distinctly from user-logged ones).
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { ActivityTimeline } from "@/components/shared/ActivityTimeline"
import type { Activity } from "@/types"

vi.mock("@/hooks/useLookups", () => ({
  useActivityTypes: () => ({
    data: [
      { id: "type-call", name: "Call" },
      { id: "type-status", name: "Status Change" },
    ],
  }),
}))

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient()
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

const baseActivity: Activity = {
  id: "a1",
  type_id: "type-call",
  logged_by: "user-1",
  lead_id: "lead-1",
  account_id: null,
  contact_id: null,
  opportunity_id: null,
  notes: "Discovery call with the client",
  is_complete: true,
  due_at: null,
  created_at: new Date().toISOString(),
}

describe("ActivityTimeline", () => {
  it("shows an empty state when there are no activities", () => {
    renderWithClient(<ActivityTimeline activities={[]} />)
    expect(screen.getByText("No activity yet.")).toBeInTheDocument()
  })

  it("renders a user-logged activity without a System marker", () => {
    renderWithClient(<ActivityTimeline activities={[baseActivity]} />)
    expect(screen.getByText("Discovery call with the client")).toBeInTheDocument()
    expect(screen.queryByText("(System)")).not.toBeInTheDocument()
  })

  it("marks a system-generated activity (null logged_by) distinctly", () => {
    const systemActivity: Activity = {
      ...baseActivity,
      id: "a2",
      type_id: "type-status",
      logged_by: null,
      notes: "Stage changed from 'Qualification' to 'Needs Analysis'.",
    }
    renderWithClient(<ActivityTimeline activities={[systemActivity]} />)
    expect(screen.getByText("(System)")).toBeInTheDocument()
  })
})
