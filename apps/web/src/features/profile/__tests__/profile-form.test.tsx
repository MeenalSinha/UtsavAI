import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProfileForm } from "@/features/profile/components/profile-form";
import { meta } from "@/test/fixtures";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh }) }));
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));
vi.mock("sonner", () => ({ toast }));
const profileApi = vi.hoisted(() => ({ update: vi.fn() }));
vi.mock("@/features/events/api", () => ({ eventsApi: {}, profileApi }));

const profile = { user_id: "u1", display_name: "Meera", preferred_locale: "en-IN", timezone: "Asia/Kolkata", email: "meera@example.com" };

beforeEach(() => vi.clearAllMocks());

describe("ProfileForm", () => {
  it("saves only permitted fields through the API", async () => {
    const user = userEvent.setup();
    profileApi.update.mockResolvedValue(profile);
    render(<ProfileForm profile={profile} meta={meta} />);
    expect(screen.getByLabelText(/^email/i)).toBeDisabled();
    const name = screen.getByLabelText(/display name/i);
    await user.clear(name);
    await user.type(name, "Meera Sharma");
    await user.click(screen.getByRole("button", { name: /save profile/i }));
    await waitFor(() => expect(profileApi.update).toHaveBeenCalledWith({ display_name: "Meera Sharma", preferred_locale: "en-IN", timezone: "Asia/Kolkata" }));
    expect(toast.success).toHaveBeenCalled();
  });

  it("requires a display name", async () => {
    const user = userEvent.setup();
    render(<ProfileForm profile={profile} meta={meta} />);
    await user.clear(screen.getByLabelText(/display name/i));
    await user.click(screen.getByRole("button", { name: /save profile/i }));
    expect(await screen.findByText(/enter your name/i)).toBeInTheDocument();
    expect(profileApi.update).not.toHaveBeenCalled();
  });
});
