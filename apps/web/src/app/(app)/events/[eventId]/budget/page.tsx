import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { BudgetWorkspace } from "@/features/budget/components/budget-workspace";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { BudgetCategoryDto, BudgetDto, BudgetSummaryDto, EventDto, ExpenseDto } from "@/types/api";

export const metadata: Metadata = { title: "BudgetAI | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventBudgetPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = await params;
  if (!UUID_RE.test(eventId)) notFound();

  const event = await loadOrNavigate(
    serverGet<EventDto>(`/events/${eventId}`),
    routes.event(eventId),
  );

  let initialBudget: BudgetDto | null = null;
  let initialCategories: BudgetCategoryDto[] = [];
  let initialExpenses: ExpenseDto[] = [];
  let initialSummary: BudgetSummaryDto | null = null;

  try {
    initialBudget = await serverGet<BudgetDto>(`/events/${eventId}/budget`);
  } catch {
    initialBudget = null;
  }

  try {
    initialCategories = await serverGet<BudgetCategoryDto[]>(`/events/${eventId}/budget/categories`);
  } catch {
    initialCategories = [];
  }

  try {
    initialExpenses = await serverGet<ExpenseDto[]>(`/events/${eventId}/expenses`);
  } catch {
    initialExpenses = [];
  }

  try {
    initialSummary = await serverGet<BudgetSummaryDto>(`/events/${eventId}/budget/summary`);
  } catch {
    initialSummary = null;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">BudgetAI Financial Management</h1>
        <p className="text-muted-foreground">
          Real-time expense tracking, category breakdown, deterministic headroom calculation, and AI budget allocation for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="budgetai" />

      <BudgetWorkspace
        event={event}
        initialBudget={initialBudget}
        initialCategories={initialCategories}
        initialExpenses={initialExpenses}
        initialSummary={initialSummary}
      />
    </div>
  );
}
