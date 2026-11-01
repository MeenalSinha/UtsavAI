import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BudgetWorkspace } from "@/features/budget/components/budget-workspace";
import * as clientApi from "@/lib/api/client";
import { makeEvent } from "@/test/fixtures";
import type { BudgetCategoryDto, BudgetDto, BudgetProposalDto, BudgetSummaryDto, ExpenseDto } from "@/types/api";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

describe("BudgetWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const event = makeEvent();

  const mockBudget: BudgetDto = {
    id: "bgt-1",
    event_id: event.id,
    total_limit: "500000.00",
    currency: "INR",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  };

  const mockCategories: BudgetCategoryDto[] = [
    {
      id: "cat-venue",
      budget_id: "bgt-1",
      category_key: "venue",
      name: "Venue & Catering",
      planned_amount: "250000.00",
      sort_order: 1,
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
      committed_amount: "50000.00",
      paid_amount: "50000.00",
      projected_amount: "100000.00",
      remaining_amount: "150000.00",
      is_over_budget: false,
    },
    {
      id: "cat-decor",
      budget_id: "bgt-1",
      category_key: "decor",
      name: "Decor & Production",
      planned_amount: "150000.00",
      sort_order: 2,
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
      committed_amount: "0.00",
      paid_amount: "0.00",
      projected_amount: "0.00",
      remaining_amount: "150000.00",
      is_over_budget: false,
    },
  ];

  const mockExpenses: ExpenseDto[] = [
    {
      id: "exp-1",
      event_id: event.id,
      budget_category_id: "cat-venue",
      description: "Palace advance deposit",
      amount: "50000.00",
      currency: "INR",
      expense_date: "2026-11-01",
      status: "paid",
      created_by: "user-1",
      created_at: "2026-11-01T10:00:00Z",
      updated_at: "2026-11-01T10:00:00Z",
    },
  ];

  const mockSummary: BudgetSummaryDto = {
    total_limit: "500000.00",
    currency: "INR",
    total_allocated: "400000.00",
    unallocated_amount: "100000.00",
    planned_expenses: "0.00",
    committed_expenses: "50000.00",
    paid_expenses: "50000.00",
    cancelled_expenses: "0.00",
    projected_total: "100000.00",
    remaining_after_committed: "450000.00",
    projected_headroom: "400000.00",
    alerts: [],
    category_summaries: [],
  };

  it("renders budget limit, allocations, and categories", () => {
    render(
      <BudgetWorkspace
        event={event}
        initialBudget={mockBudget}
        initialCategories={mockCategories}
        initialExpenses={mockExpenses}
        initialSummary={mockSummary}
      />
    );

    expect(screen.getByText("Total Spending Ceiling")).toBeInTheDocument();
    expect(screen.getByText("Venue & Catering")).toBeInTheDocument();
    expect(screen.getByText("Decor & Production")).toBeInTheDocument();
  });

  it("opens AI budget assistant and accepts recommendations", async () => {
    const user = userEvent.setup();

    const sampleAiProposal: BudgetProposalDto = {
      id: "prop-bgt-1",
      event_id: event.id,
      conversation_id: null,
      proposal_type: "budget",
      status: "proposed",
      base_revision: 1,
      payload: {
        schema_version: 1,
        summary: "Balanced Rajasthani wedding budget allocation across 6 main buckets.",
        assumptions: ["350 guests across 3 days"],
        warnings: ["Catering may increase with luxury menu items"],
        savings_recommendations: ["Book local Jaipur floral vendors directly"],
        follow_up_questions: ["Do you plan to host an alcohol bar?"],
        proposed_allocations: [
          {
            category_key: "catering",
            name: "Catering & Banquets",
            percentage: 35,
            suggested_amount: "175000.00",
            notes: "Multi-cuisine buffet",
          },
        ],
      },
      created_at: "2026-11-01T10:00:00Z",
      accepted_at: null,
    };

    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: sampleAiProposal,
      etag: null,
    });

    render(
      <BudgetWorkspace
        event={event}
        initialBudget={mockBudget}
        initialCategories={mockCategories}
        initialExpenses={mockExpenses}
        initialSummary={mockSummary}
      />
    );

    const aiButton = screen.getByRole("button", { name: /AI Budget Assistant/i });
    await user.click(aiButton);

    const textarea = screen.getByPlaceholderText(/Prioritize royal Rajasthani food/i);
    await user.type(textarea, "Suggest wedding budget allocation");

    const generateBtn = screen.getByRole("button", { name: /Generate Recommendations/i });
    await user.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByText("Balanced Rajasthani wedding budget allocation across 6 main buckets.")).toBeInTheDocument();
      expect(screen.getByText("Catering & Banquets")).toBeInTheDocument();
    });

    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: { ...sampleAiProposal, status: "accepted" },
      etag: null,
    });
    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: mockSummary,
      etag: null,
    });
    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: mockCategories,
      etag: null,
    });
    vi.mocked(clientApi.apiFetch).mockResolvedValueOnce({
      data: mockExpenses,
      etag: null,
    });

    const acceptBtn = screen.getByRole("button", { name: /Approve & Apply/i });
    await user.click(acceptBtn);

    await waitFor(() => {
      expect(screen.getByText(/Budget recommendations applied successfully/i)).toBeInTheDocument();
    });
  });
});
