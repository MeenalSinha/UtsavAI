import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PreferencesForm } from "@/features/preferences/components/preferences-form";
import * as clientApi from "@/lib/api/client";
import { makeEvent } from "@/test/fixtures";
import type { EventPreferencesDto } from "@/types/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

describe("PreferencesForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const samplePreferences: EventPreferencesDto = {
    event_id: "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
    style_tags: ["Traditional", "Royal & Grand"],
    cultural_context: {
      tradition: "Hindu / Vedic",
      regional_customs: "Rajasthani",
      special_ceremonies: "Haldi, Sangeet",
    },
    priorities: {
      key_priorities: ["Traditional Authenticity", "Catering & Culinary Variety"],
      notes: "High priority on Rajasthani cuisine",
    },
    accessibility_notes: {
      accommodations: ["Dedicated seating for elderly"],
      additional_notes: "Step-free mandap",
    },
    schema_version: 1,
    updated_at: "2026-11-01T12:00:00Z",
  };

  it("renders with initial preferences loaded", () => {
    const event = makeEvent();
    render(<PreferencesForm event={event} initialPreferences={samplePreferences} />);

    expect(screen.getByText("Aesthetic & Style Theme")).toBeInTheDocument();
    expect(screen.getByText("Cultural & Regional Heritage")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Hindu / Vedic")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Rajasthani")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Haldi, Sangeet")).toBeInTheDocument();
    expect(screen.getByDisplayValue("High priority on Rajasthani cuisine")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Step-free mandap")).toBeInTheDocument();
  });

  it("submits updated preferences through apiFetch", async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    vi.mocked(clientApi.apiFetch).mockResolvedValue({
      data: samplePreferences,
      etag: null,
    });

    render(<PreferencesForm event={event} initialPreferences={null} />);

    // Toggle a style tag
    await user.click(screen.getByRole("button", { name: "Minimalist" }));

    // Click save
    const saveButton = screen.getByRole("button", { name: /save preferences/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(clientApi.apiFetch).toHaveBeenCalledWith(
        `/events/${event.id}/preferences`,
        expect.objectContaining({
          method: "PUT",
        }),
      );
    });

    expect(await screen.findByText(/Preferences saved successfully/i)).toBeInTheDocument();
  });

  it("disables editing when event is archived", () => {
    const archivedEvent = makeEvent({ status: "archived" });
    render(<PreferencesForm event={archivedEvent} initialPreferences={samplePreferences} />);

    expect(screen.queryByRole("button", { name: /save preferences/i })).not.toBeInTheDocument();
    expect(screen.getByDisplayValue("Hindu / Vedic")).toBeDisabled();
  });
});

