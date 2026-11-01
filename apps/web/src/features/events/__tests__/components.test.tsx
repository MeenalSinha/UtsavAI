import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ArchiveEventDialog } from "@/features/events/components/archive-dialog";
import { EventList } from "@/features/events/components/event-list";
import { EventWorkspace } from "@/features/events/components/event-workspace";
import { ApiError } from "@/lib/api/errors";
import { makeEvent, meta } from "@/test/fixtures";

const push = vi.fn();
const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh }), usePathname: () => "/events/x" }));
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));
vi.mock("sonner", () => ({ toast }));
const api = vi.hoisted(() => ({ create: vi.fn(), update: vi.fn(), archive: vi.fn() }));
vi.mock("@/features/events/api", () => ({ eventsApi: api, profileApi: { update: vi.fn() } }));

beforeEach(() => vi.clearAllMocks());

describe("EventList", () => {
  it("shows a meaningful empty state and no fabricated events", () => {
    render(<EventList events={[]} />);
    expect(screen.getByText("No events yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create event/i })).toHaveAttribute("href", "/events/new");
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("renders each event with title, category, dates, location, guests and status", () => {
    render(<EventList events={[makeEvent(), makeEvent({ id: "2", title: "Second", status: "draft", location: { name: null, city: null, region: null, country_code: null } })]} />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/events/b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade");
    expect(screen.getByText("Aarav and Meera's Wedding")).toBeInTheDocument();
    expect(screen.getByText(/Jaipur Palace, Jaipur, Rajasthan/)).toBeInTheDocument();
    expect(screen.getAllByText(/300 expected guests/)).toHaveLength(2);
    expect(screen.getByText("Planning")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getAllByText(/12 Feb 2027/)).toHaveLength(2);
  });
});

describe("ArchiveEventDialog", () => {
  it("requires explicit confirmation before archiving", async () => {
    const user = userEvent.setup();
    api.archive.mockResolvedValue(undefined);
    render(<ArchiveEventDialog eventId="e1" title="My Wedding" />);
    await user.click(screen.getByRole("button", { name: /archive/i }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/archive this event/i)).toBeInTheDocument();
    expect(api.archive).not.toHaveBeenCalled();

    await user.click(within(dialog).getByRole("button", { name: /keep event/i }));
    expect(api.archive).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: /archive/i }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: /archive event/i }));
    await waitFor(() => expect(api.archive).toHaveBeenCalledWith("e1"));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/dashboard"));
    expect(toast.success).toHaveBeenCalled();
  });

  it("surfaces API failures and stays on the page", async () => {
    const user = userEvent.setup();
    api.archive.mockRejectedValue(new ApiError(403, "FORBIDDEN", "You do not have permission to perform this action."));
    render(<ArchiveEventDialog eventId="e1" title="My Wedding" />);
    await user.click(screen.getByRole("button", { name: /archive/i }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: /archive event/i }));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("You do not have permission to perform this action."));
    expect(push).not.toHaveBeenCalled();
  });
});

describe("EventWorkspace", () => {
  it("shows saved details and marks future modules as unavailable, not functional", () => {
    render(<EventWorkspace event={makeEvent()} meta={meta} />);
    expect(screen.getByRole("heading", { level: 1, name: /Aarav and Meera/ })).toBeInTheDocument();
    expect(screen.getByText("Expected guests")).toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: /event modules/i });
    for (const name of ["PlanAI", "BudgetAI", "TimelineAI", "VendorConnect", "GiftCircle"]) {
      const item = within(nav).getByText(name).closest("span[aria-disabled]");
      expect(item).toHaveAttribute("aria-disabled", "true");
    }
    expect(within(nav).getAllByText("Coming soon")).toHaveLength(5);
    expect(within(nav).getByText("Overview")).toHaveAttribute("aria-current", "page");
    expect(within(nav).queryByRole("link")).not.toBeInTheDocument();
  });

  it("lets an owner edit and archive", async () => {
    const user = userEvent.setup();
    render(<EventWorkspace event={makeEvent()} meta={meta} />);
    expect(screen.getByRole("button", { name: /archive/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /edit details/i }));
    expect(await screen.findByRole("form", { name: /edit event/i })).toBeInTheDocument();
  });

  it("hides archive for editors and all mutation controls for viewers", () => {
    const { unmount } = render(<EventWorkspace event={makeEvent({ my_role: "editor" })} meta={meta} />);
    expect(screen.getByRole("button", { name: /edit details/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /archive/i })).not.toBeInTheDocument();
    unmount();
    render(<EventWorkspace event={makeEvent({ my_role: "viewer" })} meta={meta} />);
    expect(screen.queryByRole("button", { name: /edit details/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /archive/i })).not.toBeInTheDocument();
  });

  it("renders archived events as read-only", () => {
    render(<EventWorkspace event={makeEvent({ status: "archived", archived_at: "2026-11-01T00:00:00Z" })} meta={meta} />);
    expect(screen.getByText(/archived and read-only/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /edit details/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^archive$/i })).not.toBeInTheDocument();
  });
});
