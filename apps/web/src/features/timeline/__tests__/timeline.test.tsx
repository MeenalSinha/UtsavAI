import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TimelineWorkspace } from "@/features/timeline/components/timeline-workspace";
import * as clientApi from "@/lib/api/client";
import { makeEvent } from "@/test/fixtures";
import type { FunctionDto, TaskDto, TimelineProposalDto, TimelineSummaryDto } from "@/types/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

describe("TimelineWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const event = makeEvent();

  const mockTasks: TaskDto[] = [
    {
      id: "task-1",
      event_id: event.id,
      function_id: null,
      title: "Book Venue Deposit",
      description: "Pay palace security deposit",
      due_at: "2026-12-01T12:00:00Z",
      status: "done",
      priority: "high",
      assigned_user_id: null,
      origin: "manual",
      sort_order: 1,
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
      completed_at: "2026-11-01T10:00:00Z",
      depends_on_task_ids: [],
    },
    {
      id: "task-2",
      event_id: event.id,
      function_id: null,
      title: "Confirm Sound & DJ",
      description: "Sign contract for music production",
      due_at: "2026-12-15T12:00:00Z",
      status: "todo",
      priority: "medium",
      assigned_user_id: null,
      origin: "ai_accepted",
      sort_order: 2,
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
      completed_at: null,
      depends_on_task_ids: ["task-1"],
    },
  ];

  const mockSummary: TimelineSummaryDto = {
    total_tasks: 2,
    completed_tasks: 1,
    pending_tasks: 1,
    in_progress_tasks: 0,
    blocked_tasks: 0,
    cancelled_tasks: 0,
    overdue_tasks: 0,
    upcoming_tasks: 1,
    unscheduled_tasks: 0,
    high_priority_tasks: 1,
    completion_percentage: 50,
  };

  const mockFunctions: FunctionDto[] = [
    {
      id: "fn-1",
      event_id: event.id,
      name: "Sangeet Night",
      starts_at: "2027-02-12T18:00:00Z",
      ends_at: "2027-02-12T23:00:00Z",
      location_name: "Palace Lawn",
      notes: null,
      sort_order: 1,
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
    },
  ];

  it("renders timeline tasks and metrics overview", () => {
    render(
      <TimelineWorkspace
        event={event}
        initialTasks={mockTasks}
        initialSummary={mockSummary}
        functions={mockFunctions}
      />
    );

    expect(screen.getByText("Total Tasks")).toBeInTheDocument();
    expect(screen.getByText("Book Venue Deposit")).toBeInTheDocument();
    expect(screen.getByText("Confirm Sound & DJ")).toBeInTheDocument();
  });

  it("switches to milestone view and displays tasks chronologically", async () => {
    const user = userEvent.setup();
    render(
      <TimelineWorkspace
        event={event}
        initialTasks={mockTasks}
        initialSummary={mockSummary}
        functions={mockFunctions}
      />
    );

    const milestoneBtn = screen.getByRole("button", { name: /Milestone Schedule/i });
    await user.click(milestoneBtn);

    expect(screen.getByText("Milestone Timeline")).toBeInTheDocument();
    expect(screen.getByText("PlanAI Generated")).toBeInTheDocument();
  });

  it("generates and accepts timeline schedule proposal from AI", async () => {
    const user = userEvent.setup();

    const sampleProposal: TimelineProposalDto = {
      id: "prop-time-1",
      event_id: event.id,
      conversation_id: null,
      proposal_type: "timeline",
      status: "proposed",
      base_revision: 1,
      payload: {
        schema_version: 1,
        summary: "Comprehensive 4-week pre-wedding preparation schedule.",
        assumptions: ["Outdoor venue booked"],
        warnings: ["High season in Jaipur requires advance sound permits"],
        follow_up_questions: ["Have you shortlisted bridal makeup artists?"],
        proposed_tasks: [
          {
            client_ref: "task_caterer",
            title: "Finalize Royal Rajasthani Menu Tasting",
            description: "Approve 4-course menu",
            due_at: "2026-12-20T12:00:00Z",
            priority: "high",
            function_ref: null,
            depends_on: [],
          },
        ],
      },
      created_at: "2026-11-01T10:00:00Z",
      accepted_at: null,
    };

    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: sampleProposal,
      etag: null,
    });

    render(
      <TimelineWorkspace
        event={event}
        initialTasks={mockTasks}
        initialSummary={mockSummary}
        functions={mockFunctions}
      />
    );

    const aiBtn = screen.getByRole("button", { name: /TimelineAI Schedule Assistant/i });
    await user.click(aiBtn);

    const textarea = screen.getByPlaceholderText(/Generate a complete 6-month planning timeline/i);
    await user.type(textarea, "Plan wedding schedule");

    const genBtn = screen.getByRole("button", { name: /Generate Recommended Timeline/i });
    await user.click(genBtn);

    await waitFor(() => {
      expect(screen.getByText("Comprehensive 4-week pre-wedding preparation schedule.")).toBeInTheDocument();
      expect(screen.getByText("Finalize Royal Rajasthani Menu Tasting")).toBeInTheDocument();
    });

    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: { ...sampleProposal, status: "accepted" },
      etag: null,
    });
    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: mockSummary,
      etag: null,
    });
    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: mockTasks,
      etag: null,
    });

    const acceptBtn = screen.getByRole("button", { name: /Accept & Import Selected/i });
    await user.click(acceptBtn);

    await waitFor(() => {
      expect(screen.getByText(/Successfully imported 1 tasks/i)).toBeInTheDocument();
    });
  });
});
