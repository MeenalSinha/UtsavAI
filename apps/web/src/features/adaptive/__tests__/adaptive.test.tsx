import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdaptiveDashboard } from "../components/adaptive-dashboard";
import { ChangeRequestForm } from "../components/change-request-form";
import { ImpactPreviewView } from "../components/impact-preview-view";
import { adaptiveService } from "../services/adaptive-service";
import type { ChangeProposal } from "../types";

vi.mock("../services/adaptive-service");

const mockProposal: ChangeProposal = {
  id: "prop-1234-5678",
  event_id: "event-1111-2222",
  created_by: "user-9999",
  base_revision: 3,
  request_text: "Increase guest count from 200 to 350 and shift dates by 3 days",
  requested_changes: {
    schema_version: 1,
    base_revision: 3,
    request_text: "Increase guest count from 200 to 350 and shift dates by 3 days",
    event_changes: {
      expected_guest_count: 350,
      start_at: "2027-02-15T10:00:00Z",
      end_at: "2027-02-16T10:00:00Z",
    },
    budget_changes: null,
    function_changes: [],
  },
  impact_result: {
    rules_version: "1.0.0",
    severity: "high",
    affected_modules: ["event", "budget", "timeline", "vendors"],
    affected_records: [
      {
        module: "event",
        entity_type: "event",
        entity_name: "Aarav & Meera Wedding",
        change_nature: "guest_count_updated",
        details: "Expected guest count altered from 200 to 350",
      },
      {
        module: "timeline",
        entity_type: "task",
        entity_name: "Finalize Catering Menu",
        change_nature: "due_date_shift_suggested",
        details: "Current due date should shift by +3.0 days",
      },
    ],
    calculations: [
      {
        metric: "Guest Count",
        before_value: "200",
        after_value: "350",
        delta: "+150",
        unit: "guests",
      },
    ],
    warnings: [
      {
        code: "WARN_EVENT_GUEST_CAPACITY_SHIFT",
        message: "Guest count change of 75.0% significantly alters catering and venue capacity.",
        severity: "high",
        recommended_action: "Review vendor quotes and catering allocations.",
      },
    ],
    suggested_options: [
      {
        id: "opt_reschedule_tasks",
        title: "Reschedule Active Task Deadlines",
        description: "Automatically shift active task deadlines by +3.0 days.",
        operations: [],
        selected_by_default: true,
      },
      {
        id: "opt_flag_budget_for_review",
        title: "Flag Budget Categories for Guest Scale Review",
        description: "Record an audit checkpoint on catering and venue categories.",
        operations: [],
        selected_by_default: true,
      },
    ],
  },
  ai_explanation: "This proposal scales attendee capacity by 75% and shifts tasks by 3 days.",
  status: "proposed",
  accepted_at: null,
  accepted_revision: null,
  rules_version: "1.0.0",
  schema_version: 1,
  created_at: "2026-11-01T12:00:00Z",
  updated_at: "2026-11-01T12:00:00Z",
};

describe("ImpactPreviewView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders impact summary, severity badge, affected modules, warnings, and calculations", () => {
    render(
      <ImpactPreviewView
        proposal={mockProposal}
        isOwner={true}
        onProposalUpdated={vi.fn()}
      />
    );

    expect(screen.getByText("Increase guest count from 200 to 350 and shift dates by 3 days")).toBeInTheDocument();
    expect(screen.getByText("high Impact")).toBeInTheDocument();
    expect(screen.getAllByText("event").length).toBeGreaterThan(0);
    expect(screen.getAllByText("budget").length).toBeGreaterThan(0);
    expect(screen.getAllByText("timeline").length).toBeGreaterThan(0);
    expect(screen.getAllByText("vendors").length).toBeGreaterThan(0);
    expect(screen.getByText("Guest count change of 75.0% significantly alters catering and venue capacity.")).toBeInTheDocument();
    expect(screen.getByText("Guest Count")).toBeInTheDocument();
    expect(screen.getByText("+150")).toBeInTheDocument();
    expect(screen.getByText("Reschedule Active Task Deadlines")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /approve & apply changes/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reject proposal/i })).toBeInTheDocument();
  });

  it("allows owner to approve and atomically apply changes", async () => {
    const user = userEvent.setup();
    const updatedProposal: ChangeProposal = {
      ...mockProposal,
      status: "accepted",
      accepted_revision: 4,
    };
    vi.mocked(adaptiveService.acceptProposal).mockResolvedValue(updatedProposal);
    const onUpdated = vi.fn();

    render(
      <ImpactPreviewView
        proposal={mockProposal}
        isOwner={true}
        onProposalUpdated={onUpdated}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /approve & apply changes/i });
    await user.click(approveBtn);

    await waitFor(() => {
      expect(adaptiveService.acceptProposal).toHaveBeenCalledWith(
        "event-1111-2222",
        "prop-1234-5678",
        expect.objectContaining({
          selected_option_ids: ["opt_reschedule_tasks", "opt_flag_budget_for_review"],
        })
      );
      expect(onUpdated).toHaveBeenCalledWith(updatedProposal);
    });
  });

  it("disables approve button when user is not owner", () => {
    render(
      <ImpactPreviewView
        proposal={mockProposal}
        isOwner={false}
        onProposalUpdated={vi.fn()}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /approve & apply changes/i });
    expect(approveBtn).toBeDisabled();
  });
});

describe("ChangeRequestForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("interprets natural language text with AI and populates structured fields", async () => {
    const user = userEvent.setup();
    vi.mocked(adaptiveService.interpretPrompt).mockResolvedValue({
      summary: "Increase guest count to 350",
      candidate_request: {
        base_revision: 3,
        request_text: "Increase guests to 350",
        event_changes: {
          expected_guest_count: 350,
          location_name: "Udaivilas Palace",
        },
      },
    });

    render(
      <ChangeRequestForm
        eventId="event-1111-2222"
        currentRevision={3}
        initialGuestCount={200}
        onProposalCreated={vi.fn()}
      />
    );

    const promptInput = screen.getByPlaceholderText(/express planned change/i);
    await user.type(promptInput, "We want to invite 350 guests at Udaivilas Palace");

    const interpretBtn = screen.getByRole("button", { name: /ai interpret/i });
    await user.click(interpretBtn);

    await waitFor(() => {
      expect(adaptiveService.interpretPrompt).toHaveBeenCalledWith(
        "event-1111-2222",
        "We want to invite 350 guests at Udaivilas Palace"
      );
      expect(screen.getByDisplayValue("Increase guests to 350")).toBeInTheDocument();
      expect(screen.getByDisplayValue("350")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Udaivilas Palace")).toBeInTheDocument();
    });
  });

  it("submits change proposal with structured payload", async () => {
    const user = userEvent.setup();
    vi.mocked(adaptiveService.createProposal).mockResolvedValue(mockProposal);
    const onCreated = vi.fn();

    render(
      <ChangeRequestForm
        eventId="event-1111-2222"
        currentRevision={3}
        initialGuestCount={200}
        onProposalCreated={onCreated}
      />
    );

    const titleInput = screen.getByLabelText(/proposal title/i);
    await user.type(titleInput, "Revised guest plan");

    const submitBtn = screen.getByRole("button", { name: /analyze downstream impacts/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(adaptiveService.createProposal).toHaveBeenCalledWith(
        "event-1111-2222",
        expect.objectContaining({
          base_revision: 3,
          request_text: "Revised guest plan",
        })
      );
      expect(onCreated).toHaveBeenCalledWith(mockProposal);
    });
  });
});

describe("AdaptiveDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays proposal history and revision details", async () => {
    vi.mocked(adaptiveService.listProposals).mockResolvedValue([mockProposal]);

    render(
      <AdaptiveDashboard
        eventId="event-1111-2222"
        eventTitle="Aarav & Meera Wedding"
        currentRevision={3}
        myRole="owner"
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Adaptive Planning Engine")).toBeInTheDocument();
      expect(screen.getByText("rev #3")).toBeInTheDocument();
      expect(screen.getAllByText("Increase guest count from 200 to 350 and shift dates by 3 days")).toHaveLength(2);
    });
  });
});
