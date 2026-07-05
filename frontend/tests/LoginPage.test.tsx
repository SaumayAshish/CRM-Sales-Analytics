// Traces to: FR-38 (login form validation + submission).
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi } from "vitest"

import { LoginPage } from "@/pages/auth/LoginPage"

const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ login: mockLogin }),
}))
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom")
  return { ...actual, useNavigate: () => mockNavigate }
})

describe("LoginPage", () => {
  it("shows a validation error for an invalid email without calling login", async () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText("Email"), "not-an-email")
    await user.type(screen.getByLabelText("Password"), "password123")
    await user.click(screen.getByRole("button", { name: "Sign in" }))

    expect(await screen.findByText("Enter a valid email address")).toBeInTheDocument()
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it("calls login and navigates on valid submission", async () => {
    mockLogin.mockResolvedValueOnce(undefined)
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText("Email"), "admin@northwindsales.com")
    await user.type(screen.getByLabelText("Password"), "DemoPass123!")
    await user.click(screen.getByRole("button", { name: "Sign in" }))

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith("admin@northwindsales.com", "DemoPass123!"))
    expect(mockNavigate).toHaveBeenCalledWith("/", { replace: true })
  })

  it("shows a generic error message on invalid credentials", async () => {
    mockLogin.mockRejectedValueOnce(new Error("401"))
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText("Email"), "admin@northwindsales.com")
    await user.type(screen.getByLabelText("Password"), "wrongpassword")
    await user.click(screen.getByRole("button", { name: "Sign in" }))

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument()
  })
})
