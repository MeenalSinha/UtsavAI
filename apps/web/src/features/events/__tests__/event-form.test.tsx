import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EventForm } from "@/features/events/components/event-form";
import { ApiError } from "@/lib/api/errors";
import { makeEvent, meta } from "@/test/fixtures";

const push = vi.fn();
const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh }) }));

const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));
vi.mock("sonner", () => ({ toast }));

const api = vi.hoisted(() => ({ create: vi.fn(), update: vi.fn(), archive: vi.fn() }));
vi.mock("@/features/events/api", () => ({ eventsApi: api, profileApi: { update: vi.fn() } }));

async function fillValid(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/event title/i), "Aarav and Meera");
  await user.type(screen.getByLabelText(/starts/i), "2027-02-12T10:00");
  await user.type(screen.getByLabelText(/ends/i), "2027-02-14T22:00");
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("EventForm (create)", () => {
  it("shows required-field errors and does not call the API", async () => {
    const user = userEvent.setup();
    render(<EventForm meta={meta} />);
    await user.click(screen.getByRole("button", { name: /create event/i }));
    expect(await screen.findByText(/give your event a title/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a start date/i)).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("blocks an end date before the start date", async () => {
    const user = userEvent.setup();
    render(<EventForm meta={meta} />);
    await user.type(screen.getByLabelText(/event title/i), "X");
    await user.type(screen.getByLabelText(/starts/i), "2027-02-14T10:00");
    await user.type(screen.getByLabelText(/ends/i), "2027-02-12T10:00");
    await user.click(screen.getByRole("button", { name: /create event/i }));
    expect(await screen.findByText(/end must be on or after the start/i)).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("blocks negative guest counts", async () => {
    const user = userEvent.setup();
    render(<EventForm meta={meta} />);
    await fillValid(user);
    const guests = screen.getByLabelText(/expected guests/i);
    await user.clear(guests);
    await user.type(guests, "-5");
    await user.click(screen.getByRole("button", { name: /create event/i }));
    expect(await screen.findByText(/whole number, 0 or more/i)).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("offers Wedding as the only enabled category and INR as the default currency", () => {
    render(<EventForm meta={meta} />);
    expect(screen.getByRole("option", { name: "Wedding" })).toBeEnabled();
    expect(screen.getByRole("option", { name: /birthday/i })).toBeDisabled();
    expect(screen.getByLabelText(/currency/i)).toHaveValue("INR");
    expect(screen.getByLabelText(/time zone/i)).toHaveValue("Asia/Kolkata");
  });

  it("submits the real API payload, shows a loading state and navigates to the new event", async () => {
    const user = userEvent.setup();
    let resolve!: (v: unknown) => void;
    api.create.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<EventForm meta={meta} />);
    await fillValid(user);
    await user.click(screen.getByRole("button", { name: /create event/i }));

    const busy = await screen.findByRole("button", { name: /saving/i });
    expect(busy).toBeDisabled();
    expect(api.create).toHaveBeenCalledWith(
      expect.objectContaining({
        event_type: "wedding",
        title: "Aarav and Meera",
        start_at: "2027-02-12T04:30:00.000Z",
        end_at: "2027-02-14T16:30:00.000Z",
        timezone: "Asia/Kolkata",
        currency: "INR",
        expected_guest_count: 0,
      }),
    );
    resolve(makeEvent({ id: "abc" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/events/abc"));
    expect(toast.success).toHaveBeenCalled();
  });

  it("does not claim success when the API fails and shows field-level errors from the server", async () => {
    const user = userEvent.setup();
    api.create.mockRejectedValue(
      new ApiError(422, "VALIDATION_ERROR", "The title is invalid.", { fields: [{ field: "title", message: "Server says no." }] }, "req_1"),
    );
    render(<EventForm meta={meta} />);
    await fillValid(user);
    await user.click(screen.getByRole("button", { name: /create event/i }));
    expect(await screen.findByText("Server says no.")).toBeInTheDocument();
    expect(toast.success).not.toHaveBeenCalled();
    expect(toast.error).toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it("shows a general error for unexpected failures", async () => {
    const user = userEvent.setup();
    api.create.mockRejectedValue(new ApiError(503, "DEPENDENCY_UNAVAILABLE", "x"));
    render(<EventForm meta={meta} />);
    await fillValid(user);
    await user.click(screen.getByRole("button", { name: /create event/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/temporarily unavailable/i);
  });
});

describe("EventForm (edit)", () => {
  it("prefills from the event in its own time zone and sends If-Match revision on save", async () => {
    const user = userEvent.setup();
    const event = makeEvent({ revision: 4 });
    api.update.mockResolvedValue(makeEvent({ revision: 5, title: "Renamed" }));
    const onSaved = vi.fn();
    render(<EventForm meta={meta} event={event} onSaved={onSaved} />);
    expect(screen.getByLabelText(/event title/i)).toHaveValue("Aarav and Meera's Wedding");
    expect(screen.getByLabelText(/starts/i)).toHaveValue("2027-02-12T10:00");
    expect(screen.getByLabelText(/category/i)).toBeDisabled();

    const title = screen.getByLabelText(/event title/i);
    await user.clear(title);
    await user.type(title, "Renamed");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(api.update).toHaveBeenCalled());
    const [id, body, revision] = api.update.mock.calls[0]!;
    expect(id).toBe(event.id);
    expect(revision).toBe(4);
    expect(body.title).toBe("Renamed");
    expect(body).not.toHaveProperty("event_type");
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
  });

  it("explains a revision conflict and offers a reload", async () => {
    const user = userEvent.setup();
    api.update.mockRejectedValue(new ApiError(409, "REVISION_CONFLICT", "changed", { current_revision: 7 }));
    render(<EventForm meta={meta} event={makeEvent()} />);
    await user.click(screen.getByRole("button", { name: /save changes/i }));
    expect(await screen.findByText(/changed by someone else/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /reload the latest version/i }));
    expect(refresh).toHaveBeenCalled();
  });
});
