// Traces to: FR-45 (client-side role gating).
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { RoleGuard } from "@/components/shared/RoleGuard"

const mockUseAuth = vi.fn()
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}))

describe("RoleGuard", () => {
  it("renders children when the current role is allowed", () => {
    mockUseAuth.mockReturnValue({ role: "Admin" })
    render(
      <RoleGuard allow={["Admin", "Manager"]}>
        <div>secret content</div>
      </RoleGuard>
    )
    expect(screen.getByText("secret content")).toBeInTheDocument()
  })

  it("does not render children when the current role is not allowed", () => {
    mockUseAuth.mockReturnValue({ role: "Rep" })
    render(
      <RoleGuard allow={["Admin", "Manager"]}>
        <div>secret content</div>
      </RoleGuard>
    )
    expect(screen.queryByText("secret content")).not.toBeInTheDocument()
  })

  it("renders the fallback when provided and access is denied", () => {
    mockUseAuth.mockReturnValue({ role: "Viewer" })
    render(
      <RoleGuard allow={["Admin"]} fallback={<div>not allowed</div>}>
        <div>secret content</div>
      </RoleGuard>
    )
    expect(screen.getByText("not allowed")).toBeInTheDocument()
    expect(screen.queryByText("secret content")).not.toBeInTheDocument()
  })

  it("denies access when role is null (unauthenticated)", () => {
    mockUseAuth.mockReturnValue({ role: null })
    render(
      <RoleGuard allow={["Admin", "Manager", "Rep", "Viewer"]}>
        <div>secret content</div>
      </RoleGuard>
    )
    expect(screen.queryByText("secret content")).not.toBeInTheDocument()
  })
})
