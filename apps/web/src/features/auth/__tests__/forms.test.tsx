import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ForgotPasswordForm, SignInForm, SignUpForm } from "@/features/auth/components/forms";

const actions = vi.hoisted(() => ({
  signInAction: vi.fn(),
  signUpAction: vi.fn(),
  forgotPasswordAction: vi.fn(),
  resetPasswordAction: vi.fn(),
}));
vi.mock("@/features/auth/actions", () => actions);

beforeEach(() => vi.clearAllMocks());

describe("SignInForm", () => {
  it("validates on the client before calling the server action", async () => {
    const user = userEvent.setup();
    render(<SignInForm />);
    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText(/valid email address/i)).toBeInTheDocument();
    expect(screen.getByText(/enter your password/i)).toBeInTheDocument();
    expect(actions.signInAction).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/email/i)).toHaveAttribute("aria-invalid", "true");
  });

  it("submits valid credentials to the server action (never handled in the browser)", async () => {
    const user = userEvent.setup();
    actions.signInAction.mockResolvedValue({ ok: false, message: "The email or password is incorrect." });
    render(<SignInForm next="/events/abc" />);
    await user.type(screen.getByLabelText(/email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/^password/i), "correct-horse1");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => expect(actions.signInAction).toHaveBeenCalled());
    const formData = actions.signInAction.mock.calls[0]![1] as FormData;
    expect(formData.get("email")).toBe("asha@example.com");
    expect(formData.get("next")).toBe("/events/abc");
    expect(await screen.findByRole("alert")).toHaveTextContent("The email or password is incorrect.");
  });

  it("shows the session-expired notice", () => {
    render(<SignInForm notice="Your session has ended. Please sign in again." />);
    expect(screen.getByRole("status")).toHaveTextContent(/session has ended/i);
  });

  it("links to password recovery", () => {
    render(<SignInForm />);
    expect(screen.getByRole("link", { name: /forgot password/i })).toHaveAttribute("href", "/forgot-password");
  });
});

describe("SignUpForm", () => {
  it("enforces password rules and confirmation", async () => {
    const user = userEvent.setup();
    render(<SignUpForm />);
    await user.type(screen.getByLabelText(/your name/i), "Asha");
    await user.type(screen.getByLabelText(/^email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/^password/i), "short");
    await user.type(screen.getByLabelText(/confirm password/i), "other");
    await user.click(screen.getByRole("button", { name: /create account/i }));
    expect(await screen.findByText(/at least 8 characters/i, { selector: "p[role=alert]" })).toBeInTheDocument();
    expect(screen.getByText(/do not match/i)).toBeInTheDocument();
    expect(actions.signUpAction).not.toHaveBeenCalled();
  });

  it("shows the verification message after a successful sign-up", async () => {
    const user = userEvent.setup();
    actions.signUpAction.mockResolvedValue({ ok: true, message: "Check your email for a verification link to finish creating your account." });
    render(<SignUpForm />);
    await user.type(screen.getByLabelText(/your name/i), "Asha");
    await user.type(screen.getByLabelText(/^email/i), "asha@example.com");
    await user.type(screen.getByLabelText(/^password/i), "abcdefg1");
    await user.type(screen.getByLabelText(/confirm password/i), "abcdefg1");
    await user.click(screen.getByRole("button", { name: /create account/i }));
    expect(await screen.findByText(/check your email/i)).toBeInTheDocument();
  });
});

describe("ForgotPasswordForm", () => {
  it("confirms without revealing whether the account exists", async () => {
    const user = userEvent.setup();
    actions.forgotPasswordAction.mockResolvedValue({ ok: true, message: "If an account exists for that email, a password reset link is on its way." });
    render(<ForgotPasswordForm />);
    await user.type(screen.getByLabelText(/email/i), "anyone@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));
    expect(await screen.findByText(/if an account exists/i)).toBeInTheDocument();
  });
});
