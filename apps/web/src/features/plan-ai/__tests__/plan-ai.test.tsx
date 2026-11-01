import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlanAiWorkspace } from "@/features/plan-ai/components/plan-ai-workspace";
import * as clientApi from "@/lib/api/client";
import { makeEvent } from "@/test/fixtures";
import type { PlanAcceptResponseDto, PlanProposalDto } from "@/types/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

describe("PlanAiWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const sampleProposal: PlanProposalDto = {
    proposal_id: "prop-123",
    event_id: "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
    conversation_id: "conv-456",
    base_revision: 1,
    status: "proposed",
    schema_version: 1,
    payload: {
      schema_version: 1,
      summary: "A 3-day royal Rajasthani celebration tailored to 350 guests.",
      assumptions: ["Outdoor venue has weather contingency"],
      warnings: ["High season in Jaipur requires advance sound permits"],
      follow_up_questions: ["Have you shortlisted bridal makeup artists?"],
      theme_suggestions: ["Royal Marwar Opulence"],
      proposed_functions: [
        {
          client_ref: "fn_sangeet",
          name: "Sangeet & Musical Night",
          starts_at: "2027-02-12T18:00:00Z",
          ends_at: "2027-02-12T23:00:00Z",
          location_name: "Palace Courtyard",
          notes: "Live folk & DJ performances",
          sort_order: 1,
        },
        {
          client_ref: "fn_pheras",
          name: "Vedic Pheras",
          starts_at: "2027-02-13T10:00:00Z",
          ends_at: "2027-02-13T14:00:00Z",
          location_name: "Lakeside Mandap",
          notes: "Traditional rituals",
          sort_order: 2,
        },
      ],
      proposed_tasks: [
        {
          client_ref: "task_sound",
          title: "Book sound & lighting vendor for Sangeet",
          description: "Reserve 10kW line array audio",
          due_at: "2026-12-01T12:00:00Z",
          priority: "high",
          function_ref: "fn_sangeet",
          depends_on: [],
        },
      ],
      planning_notes: ["Ensure adequate seating for elderly guests during Pheras"],
    },
    created_at: "2026-11-01T12:00:00Z",
    accepted_at: null,
    model_metadata: { model: "gemini-2.5-flash" },
  };

  const acceptResponse: PlanAcceptResponseDto = {
    proposal_id: sampleProposal.proposal_id,
    status: "accepted",
    new_revision: 2,
    accepted_functions_count: 2,
    accepted_tasks_count: 1,
    created_function_ids: ["fn-1", "fn-2"],
    created_task_ids: ["t-1"],
  };

  it("renders welcome assistant card when no active conversation", () => {
    const event = makeEvent();
    render(<PlanAiWorkspace event={event} initialConversations={[]} />);

    expect(screen.getByText("PlanAI Wedding Assistant")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask PlanAI: e.g./i)).toBeInTheDocument();
  });

  it("submits prompt, receives proposal, and renders recommendations", async () => {
    const user = userEvent.setup();
    const event = makeEvent();

    vi.mocked(clientApi.apiFetch).mockImplementation((path: string) => {
      if (path.includes("/plans/generate")) {
        return Promise.resolve({ data: sampleProposal, etag: null });
      }
      if (path.includes("/ai/conversations/")) {
        return Promise.resolve({
          data: {
            id: "conv-456",
            event_id: event.id,
            user_id: "u1",
            title: "Plan",
            created_at: "2026-11-01T12:00:00Z",
            updated_at: "2026-11-01T12:00:00Z",
            messages: [],
          },
          etag: null,
        });
      }
      if (path.includes("/ai/conversations")) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: "conv-456",
                event_id: event.id,
                user_id: "u1",
                title: "Rajasthani Wedding",
                created_at: "2026-11-01T12:00:00Z",
                updated_at: "2026-11-01T12:00:00Z",
              },
            ],
          },
          etag: null,
        });
      }
      return Promise.resolve({ data: null, etag: null });
    });

    render(<PlanAiWorkspace event={event} initialConversations={[]} />);

    const input = screen.getByPlaceholderText(/Ask PlanAI: e.g./i);
    await user.type(input, "Plan our royal wedding with 350 guests");

    const generateBtn = screen.getByRole("button", { name: /generate/i });
    await user.click(generateBtn);

    await waitFor(() => {
      expect(clientApi.apiFetch).toHaveBeenCalledWith(
        `/events/${event.id}/plans/generate`,
        expect.objectContaining({
          method: "POST",
          json: expect.objectContaining({
            request: "Plan our royal wedding with 350 guests",
          }),
        }),
      );
    });

    // Verify proposal review card elements
    expect(await screen.findByText("AI-Generated Plan Proposal")).toBeInTheDocument();
    expect(screen.getByText(sampleProposal.payload.summary)).toBeInTheDocument();
    expect(screen.getByText("Sangeet & Musical Night")).toBeInTheDocument();
    expect(screen.getByText("Vedic Pheras")).toBeInTheDocument();
    expect(screen.getByText("Book sound & lighting vendor for Sangeet")).toBeInTheDocument();
    expect(screen.getByText("Outdoor venue has weather contingency")).toBeInTheDocument();
  });

  it("accepts selected recommendations and shows confirmation", async () => {
    const user = userEvent.setup();
    const event = makeEvent({ revision: 1 });

    vi.mocked(clientApi.apiFetch).mockImplementation((path: string) => {
      if (path.includes("/plans/generate")) {
        return Promise.resolve({ data: sampleProposal, etag: null });
      }
      if (path.includes("/accept")) {
        return Promise.resolve({ data: acceptResponse, etag: null });
      }
      if (path.includes("/ai/conversations/")) {
        return Promise.resolve({
          data: {
            id: "conv-456",
            event_id: event.id,
            user_id: "u1",
            title: "Plan",
            created_at: "2026-11-01T12:00:00Z",
            updated_at: "2026-11-01T12:00:00Z",
            messages: [],
          },
          etag: null,
        });
      }
      if (path.includes("/ai/conversations")) {
        return Promise.resolve({ data: { items: [] }, etag: null });
      }
      return Promise.resolve({ data: null, etag: null });
    });

    render(<PlanAiWorkspace event={event} initialConversations={[]} />);

    const input = screen.getByPlaceholderText(/Ask PlanAI: e.g./i);
    await user.type(input, "Plan our wedding");
    await user.click(screen.getByRole("button", { name: /generate/i }));

    const acceptBtn = await screen.findByRole("button", { name: /accept selected/i });
    await user.click(acceptBtn);

    await waitFor(() => {
      expect(clientApi.apiFetch).toHaveBeenCalledWith(
        `/events/${event.id}/ai/proposals/${sampleProposal.proposal_id}/accept`,
        expect.objectContaining({
          method: "POST",
          json: expect.objectContaining({
            base_revision: 1,
            selected_function_refs: ["fn_sangeet", "fn_pheras"],
            selected_task_refs: ["task_sound"],
          }),
        }),
      );
    });

    expect(
      await screen.findByText(/Successfully saved 2 ceremonies and 1 starter tasks/i),
    ).toBeInTheDocument();
  });

  it("displays stale warning when event revision has advanced beyond proposal base revision", async () => {
    const user = userEvent.setup();
    // Event revision is 5, but proposal base_revision is 1
    const event = makeEvent({ revision: 5 });

    vi.mocked(clientApi.apiFetch).mockImplementation((path: string) => {
      if (path.includes("/plans/generate")) {
        return Promise.resolve({ data: sampleProposal, etag: null });
      }
      if (path.includes("/ai/conversations/")) {
        return Promise.resolve({
          data: {
            id: "conv-456",
            event_id: event.id,
            user_id: "u1",
            title: "Plan",
            created_at: "2026-11-01T12:00:00Z",
            updated_at: "2026-11-01T12:00:00Z",
            messages: [],
          },
          etag: null,
        });
      }
      return Promise.resolve({ data: { items: [] }, etag: null });
    });

    render(<PlanAiWorkspace event={event} initialConversations={[]} />);

    const input = screen.getByPlaceholderText(/Ask PlanAI: e.g./i);
    await user.type(input, "Suggest plan");
    await user.click(screen.getByRole("button", { name: /generate/i }));

    expect(await screen.findByText(/Stale Revision/i)).toBeInTheDocument();
  });
});
