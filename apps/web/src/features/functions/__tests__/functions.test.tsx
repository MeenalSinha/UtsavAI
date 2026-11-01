import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FunctionList } from "@/features/functions/components/function-list";
import * as clientApi from "@/lib/api/client";
import { makeEvent } from "@/test/fixtures";
import type { EventFunctionDto } from "@/types/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

describe("FunctionList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const sampleFunctions: EventFunctionDto[] = [
    {
      id: "f1",
      event_id: "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
      name: "Mehendi & Sangeet",
      starts_at: "2027-02-12T16:00:00Z",
      ends_at: "2027-02-12T22:00:00Z",
      location_name: "Palace Lawn",
      notes: "Pastel theme",
      sort_order: 1,
      created_at: "2026-11-01T12:00:00Z",
      updated_at: "2026-11-01T12:00:00Z",
    },
    {
      id: "f2",
      event_id: "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
      name: "Saat Phere",
      starts_at: "2027-02-13T10:00:00Z",
      ends_at: "2027-02-13T14:00:00Z",
      location_name: "Mandap Hall",
      notes: "Traditional rituals",
      sort_order: 2,
      created_at: "2026-11-01T12:00:00Z",
      updated_at: "2026-11-01T12:00:00Z",
    },
  ];

  it("renders empty state when there are no ceremonies", () => {
    const event = makeEvent();
    render(<FunctionList event={event} initialFunctions={[]} />);

    expect(screen.getByText("No functions added yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add first function/i })).toBeInTheDocument();
  });

  it("renders function cards in order", () => {
    const event = makeEvent();
    render(<FunctionList event={event} initialFunctions={sampleFunctions} />);

    expect(screen.getByText("Mehendi & Sangeet")).toBeInTheDocument();
    expect(screen.getByText("Saat Phere")).toBeInTheDocument();
    expect(screen.getByText("Palace Lawn")).toBeInTheDocument();
    expect(screen.getByText("Mandap Hall")).toBeInTheDocument();
    expect(screen.getByText("Pastel theme")).toBeInTheDocument();
  });

  it("opens create function dialog and creates function", async () => {
    const user = userEvent.setup();
    const event = makeEvent();

    const createdFn: EventFunctionDto = {
      id: "f3",
      event_id: event.id,
      name: "Reception Gala",
      starts_at: null,
      ends_at: null,
      location_name: "Grand Ballroom",
      notes: null,
      sort_order: 3,
      created_at: "2026-11-01T12:00:00Z",
      updated_at: "2026-11-01T12:00:00Z",
    };

    vi.mocked(clientApi.apiFetch).mockResolvedValue({
      data: createdFn,
      etag: null,
    });

    render(<FunctionList event={event} initialFunctions={sampleFunctions} />);

    const addBtn = screen.getByRole("button", { name: /add function/i });
    await user.click(addBtn);

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Add Function" })).toBeInTheDocument();

    const nameInput = within(dialog).getByLabelText(/function name \*/i);
    await user.type(nameInput, "Reception Gala");

    const submitBtn = within(dialog).getByRole("button", { name: "Add Function" });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(clientApi.apiFetch).toHaveBeenCalledWith(
        `/events/${event.id}/functions`,
        expect.objectContaining({
          method: "POST",
          json: expect.objectContaining({ name: "Reception Gala" }),
        }),
      );
    });

    expect(await screen.findByText("Reception Gala")).toBeInTheDocument();
  });

  it("does not allow adding when archived", () => {
    const archivedEvent = makeEvent({ status: "archived" });
    render(<FunctionList event={archivedEvent} initialFunctions={sampleFunctions} />);

    expect(screen.queryByRole("button", { name: /add function/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
  });
});
