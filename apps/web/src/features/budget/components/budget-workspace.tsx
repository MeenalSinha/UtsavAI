"use client";

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Loader2,
  PieChart,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import type {
  BudgetCategoryDto,
  BudgetDto,
  BudgetProposalDto,
  BudgetSummaryDto,
  EventDto,
  ExpenseDto,
  ExpenseStatus,
} from "@/types/api";

interface BudgetWorkspaceProps {
  event: EventDto;
  initialBudget: BudgetDto | null;
  initialCategories: BudgetCategoryDto[];
  initialExpenses: ExpenseDto[];
  initialSummary: BudgetSummaryDto | null;
}

export function BudgetWorkspace({
  event,
  initialBudget,
  initialCategories,
  initialExpenses,
  initialSummary,
}: BudgetWorkspaceProps) {
  const [budget, setBudget] = React.useState<BudgetDto | null>(initialBudget);
  const [categories, setCategories] = React.useState<BudgetCategoryDto[]>(initialCategories);
  const [expenses, setExpenses] = React.useState<ExpenseDto[]>(initialExpenses);
  const [summary, setSummary] = React.useState<BudgetSummaryDto | null>(initialSummary);

  const [activeTab, setActiveTab] = React.useState<"overview" | "categories" | "expenses">("overview");

  // Budget limit modal / state
  const [editingLimit, setEditingLimit] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState(initialBudget?.total_limit || "0.00");
  const [savingLimit, setSavingLimit] = React.useState(false);

  // Category modal
  const [categoryModalOpen, setCategoryModalOpen] = React.useState(false);
  const [catKey, setCatKey] = React.useState("");
  const [catName, setCatName] = React.useState("");
  const [catPlanned, setCatPlanned] = React.useState("0.00");
  const [savingCategory, setSavingCategory] = React.useState(false);

  // Expense modal
  const [expenseModalOpen, setExpenseModalOpen] = React.useState(false);
  const [expCategory, setExpCategory] = React.useState("");
  const [expDesc, setExpDesc] = React.useState("");
  const [expAmount, setExpAmount] = React.useState("");
  const [expStatus, setExpStatus] = React.useState<ExpenseStatus>("planned");
  const [savingExpense, setSavingExpense] = React.useState(false);

  // Expense filters
  const [filterCategory, setFilterCategory] = React.useState("all");
  const [filterStatus, setFilterStatus] = React.useState("all");
  const [searchQuery, setSearchQuery] = React.useState("");

  // AI assistant state
  const [aiModalOpen, setAiModalOpen] = React.useState(false);
  const [aiPrompt, setAiPrompt] = React.useState("");
  const [aiGenerating, setAiGenerating] = React.useState(false);
  const [aiProposal, setAiProposal] = React.useState<BudgetProposalDto | null>(null);
  const [selectedCatKeys, setSelectedCatKeys] = React.useState<Set<string>>(new Set());
  const [aiAccepting, setAiAccepting] = React.useState(false);

  const [error, setError] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  const refreshSummary = async () => {
    try {
      const res = await apiFetch<BudgetSummaryDto>(`/api/v1/events/${event.id}/budget/summary`);
      setSummary(res.data);
      const catRes = await apiFetch<BudgetCategoryDto[]>(`/api/v1/events/${event.id}/budget/categories`);
      setCategories(catRes.data);
      const expRes = await apiFetch<ExpenseDto[]>(`/api/v1/events/${event.id}/expenses`);
      setExpenses(expRes.data);
    } catch {
      // quiet refresh fail
    }
  };

  const handleSaveBudgetLimit = async () => {
    setSavingLimit(true);
    setError(null);
    try {
      const res = await apiFetch<BudgetDto>(`/api/v1/events/${event.id}/budget`, {
        method: budget ? "PATCH" : "POST",
        json: { total_limit: limitInput },
      });
      setBudget(res.data);
      setEditingLimit(false);
      setSuccessMsg("Budget limit updated successfully.");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingLimit(false);
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCategory(true);
    setError(null);
    try {
      await apiFetch<BudgetCategoryDto>(`/api/v1/events/${event.id}/budget/categories`, {
        method: "POST",
        json: {
          category_key: catKey.toLowerCase().replace(/[^a-z0-9_]/g, "_"),
          name: catName,
          planned_amount: catPlanned,
        },
      });
      setCategoryModalOpen(false);
      setCatKey("");
      setCatName("");
      setCatPlanned("0.00");
      setSuccessMsg("Category created successfully.");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingCategory(false);
    }
  };

  const handleDeleteCategory = async (catId: string) => {
    if (!confirm("Are you sure you want to delete this category?")) return;
    setError(null);
    try {
      await apiFetch(`/api/v1/events/${event.id}/budget/categories/${catId}`, {
        method: "DELETE",
      });
      setSuccessMsg("Category deleted.");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expCategory) {
      setError("Please select a budget category.");
      return;
    }
    setSavingExpense(true);
    setError(null);
    try {
      await apiFetch<ExpenseDto>(`/api/v1/events/${event.id}/expenses`, {
        method: "POST",
        json: {
          budget_category_id: expCategory,
          description: expDesc,
          amount: expAmount,
          status: expStatus,
        },
      });
      setExpenseModalOpen(false);
      setExpDesc("");
      setExpAmount("");
      setSuccessMsg("Expense recorded.");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSavingExpense(false);
    }
  };

  const handleUpdateExpenseStatus = async (expId: string, newStatus: ExpenseStatus) => {
    try {
      await apiFetch<ExpenseDto>(`/api/v1/events/${event.id}/expenses/${expId}`, {
        method: "PATCH",
        json: { status: newStatus },
      });
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleDeleteExpense = async (expId: string) => {
    if (!confirm("Are you sure you want to delete this expense?")) return;
    try {
      await apiFetch(`/api/v1/events/${event.id}/expenses/${expId}`, {
        method: "DELETE",
      });
      setSuccessMsg("Expense removed.");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleGenerateBudgetProposal = async () => {
    if (!aiPrompt.trim()) return;
    setAiGenerating(true);
    setError(null);
    try {
      const res = await apiFetch<BudgetProposalDto>(`/api/v1/events/${event.id}/budget/ai/generate`, {
        method: "POST",
        json: { prompt: aiPrompt },
      });
      setAiProposal(res.data);
      setSelectedCatKeys(new Set(res.data.payload.proposed_allocations.map((a) => a.category_key)));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setAiGenerating(false);
    }
  };

  const handleAcceptBudgetProposal = async () => {
    if (!aiProposal) return;
    setAiAccepting(true);
    setError(null);
    try {
      await apiFetch<BudgetProposalDto>(
        `/api/v1/events/${event.id}/budget/ai/proposals/${aiProposal.id}/accept`,
        {
          method: "POST",
          json: {
            base_revision: aiProposal.base_revision,
            selected_category_keys: Array.from(selectedCatKeys),
          },
        },
      );
      setAiModalOpen(false);
      setAiProposal(null);
      setSuccessMsg("Budget recommendations applied successfully!");
      await refreshSummary();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setAiAccepting(false);
    }
  };

  const filteredExpenses = expenses.filter((e) => {
    if (filterCategory !== "all" && e.budget_category_id !== filterCategory) return false;
    if (filterStatus !== "all" && e.status !== filterStatus) return false;
    if (searchQuery && !e.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const currency = summary?.currency || event.currency || "INR";
  const totalLimitNum = summary ? parseFloat(summary.total_limit) : 0;
  const committedPaidNum = summary ? parseFloat(summary.committed_expenses) + parseFloat(summary.paid_expenses) : 0;
  const spentPercent = totalLimitNum > 0 ? Math.min(100, Math.round((committedPaidNum / totalLimitNum) * 100)) : 0;

  return (
    <div className="space-y-6">
      {/* Top Banner & AI Assistant button */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">BudgetAI Workspace</h1>
          <p className="text-sm text-muted-foreground">
            Authoritative financial management, deterministic expense tracking, and AI budget distribution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refreshSummary}>
            <RefreshCw className="mr-1.5 h-4 w-4" /> Refresh
          </Button>
          <Button
            className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700"
            size="sm"
            onClick={() => {
              setAiModalOpen(true);
              setError(null);
            }}
          >
            <Sparkles className="mr-1.5 h-4 w-4" /> AI Budget Assistant
          </Button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
          <Button variant="ghost" size="sm" className="ml-auto h-6 w-6 p-0" onClick={() => setError(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
      {successMsg && (
        <div className="flex items-center gap-2 rounded-md border border-emerald-500/50 bg-emerald-50 p-3 text-sm text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
          <Button variant="ghost" size="sm" className="ml-auto h-6 w-6 p-0" onClick={() => setSuccessMsg(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Deterministic Financial Alerts */}
      {summary?.alerts && summary.alerts.length > 0 && (
        <div className="space-y-2">
          {summary.alerts.map((alertText, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2.5 rounded-lg border border-amber-500/40 bg-amber-50/70 p-3 text-sm text-amber-900 dark:bg-amber-950/30 dark:text-amber-200"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <span>{alertText}</span>
            </div>
          ))}
        </div>
      )}

      {/* Financial Overview Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Budget Card */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between">
              <span>Total Spending Ceiling</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-primary"
                onClick={() => {
                  setEditingLimit(true);
                  setLimitInput(summary?.total_limit || "0.00");
                }}
              >
                Edit
              </Button>
            </CardDescription>
            <CardTitle className="text-2xl font-bold">
              {currency} {Number(summary?.total_limit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Allocated: {currency} {Number(summary?.total_allocated || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>

        {/* Committed & Paid */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Committed & Paid</CardDescription>
            <CardTitle className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
              {currency} {Number(committedPaidNum).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Paid: {currency} {Number(summary?.paid_expenses || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })} | Committed: {currency} {Number(summary?.committed_expenses || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>

        {/* Projected Headroom */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Projected Headroom</CardDescription>
            <CardTitle
              className={`text-2xl font-bold ${
                summary && parseFloat(summary.projected_headroom) < 0
                  ? "text-destructive"
                  : "text-emerald-600 dark:text-emerald-400"
              }`}
            >
              {currency} {Number(summary?.projected_headroom || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Projected Total: {currency} {Number(summary?.projected_total || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>

        {/* Unallocated Amount */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Unallocated Reserve</CardDescription>
            <CardTitle className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {currency} {Number(summary?.unallocated_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Remaining after committed: {currency} {Number(summary?.remaining_after_committed || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5 rounded-lg border bg-card p-4">
        <div className="flex justify-between text-xs font-medium">
          <span>Committed & Paid Spend: {spentPercent}% of total ceiling</span>
          <span>{currency} {Number(committedPaidNum).toLocaleString("en-IN")} / {currency} {Number(totalLimitNum).toLocaleString("en-IN")}</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={`h-full transition-all ${
              spentPercent > 100 ? "bg-destructive" : spentPercent > 80 ? "bg-amber-500" : "bg-primary"
            }`}
            style={{ width: `${Math.min(100, spentPercent)}%` }}
          />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab("overview")}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "overview"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Categories Breakdown ({categories.length})
        </button>
        <button
          onClick={() => setActiveTab("expenses")}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "expenses"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Expense Tracker ({expenses.length})
        </button>
      </div>

      {/* TAB 1: CATEGORIES BREAKDOWN */}
      {activeTab === "overview" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Planned Categories & Allocations</h2>
            <Button size="sm" onClick={() => setCategoryModalOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" /> Add Category
            </Button>
          </div>

          {categories.length === 0 ? (
            <Card className="flex flex-col items-center justify-center p-8 text-center">
              <PieChart className="mb-3 h-10 w-10 text-muted-foreground" />
              <CardTitle className="text-base">No budget categories established yet</CardTitle>
              <CardDescription className="mb-4 text-sm">
                Create custom categories or use the AI Budget Assistant to generate a regional allocation plan.
              </CardDescription>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => setCategoryModalOpen(true)}>
                  Create First Category
                </Button>
                <Button variant="outline" size="sm" onClick={() => setAiModalOpen(true)}>
                  <Sparkles className="mr-1.5 h-4 w-4 text-indigo-500" /> Generate with AI
                </Button>
              </div>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {categories.map((c) => {
                const plannedNum = parseFloat(c.planned_amount);
                const spentNum = parseFloat(c.paid_amount) + parseFloat(c.committed_amount);
                const catPercent = plannedNum > 0 ? Math.min(100, Math.round((spentNum / plannedNum) * 100)) : 0;

                return (
                  <Card key={c.id} className="relative overflow-hidden">
                    {c.is_over_budget && (
                      <div className="absolute right-3 top-3">
                        <Badge variant="warning" className="text-xs">
                          Over Budget
                        </Badge>
                      </div>
                    )}
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base font-semibold">{c.name}</CardTitle>
                      <CardDescription className="text-xs font-mono">{c.category_key}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 pb-3">
                      <div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Planned Allocation</span>
                          <span className="font-semibold text-foreground">
                            {currency} {Number(c.planned_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                        <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                          <span>Spent / Committed</span>
                          <span>{currency} {Number(spentNum).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                          <span>Remaining</span>
                          <span className={c.is_over_budget ? "font-bold text-destructive" : ""}>
                            {currency} {Number(c.remaining_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      </div>

                      {/* Mini progress */}
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                        <div
                          className={`h-full ${c.is_over_budget ? "bg-destructive" : "bg-primary"}`}
                          style={{ width: `${catPercent}%` }}
                        />
                      </div>
                    </CardContent>
                    <CardFooter className="flex justify-end gap-1 border-t pt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-2 text-destructive hover:bg-destructive/10"
                        onClick={() => handleDeleteCategory(c.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXPENSE TRACKER */}
      {activeTab === "expenses" && (
        <div className="space-y-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div className="flex flex-wrap items-center gap-2">
              {/* Category filter */}
              <select
                aria-label="Filter expenses by category"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="h-9 rounded-md border bg-background px-3 text-xs"
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              {/* Status filter */}
              <select
                aria-label="Filter expenses by status"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="h-9 rounded-md border bg-background px-3 text-xs"
              >
                <option value="all">All Statuses</option>
                <option value="planned">Planned</option>
                <option value="committed">Committed</option>
                <option value="paid">Paid</option>
                <option value="cancelled">Cancelled</option>
              </select>

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search description..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-9 w-44 pl-8 text-xs sm:w-60"
                />
              </div>
            </div>

            <Button size="sm" onClick={() => setExpenseModalOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" /> Add Expense
            </Button>
          </div>

          {filteredExpenses.length === 0 ? (
            <Card className="flex flex-col items-center justify-center p-8 text-center">
              <DollarSign className="mb-3 h-10 w-10 text-muted-foreground" />
              <CardTitle className="text-base">No expenses matching current filters</CardTitle>
              <CardDescription className="mb-4 text-sm">
                Record new vendor payments, deposits, or planned costs.
              </CardDescription>
              <Button size="sm" onClick={() => setExpenseModalOpen(true)}>
                Add First Expense
              </Button>
            </Card>
          ) : (
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-left text-sm">
                <thead className="border-b bg-muted/50 text-xs text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Description</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Amount</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredExpenses.map((exp) => {
                    const catObj = categories.find((c) => c.id === exp.budget_category_id);
                    return (
                      <tr key={exp.id} className="hover:bg-muted/30">
                        <td className="px-4 py-3 font-medium">{exp.description}</td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">{catObj?.name || "Unassigned"}</td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">{exp.expense_date}</td>
                        <td className="px-4 py-3 font-semibold">
                          {currency} {Number(exp.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3">
                          <select
                            aria-label={`Change status for expense: ${exp.description}`}
                            value={exp.status}
                            onChange={(e) => handleUpdateExpenseStatus(exp.id, e.target.value as ExpenseStatus)}
                            className={`h-7 rounded border px-2 text-xs font-medium ${
                              exp.status === "paid"
                                ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                                : exp.status === "committed"
                                ? "bg-indigo-50 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                                : exp.status === "cancelled"
                                ? "bg-muted text-muted-foreground line-through"
                                : "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            }`}
                          >
                            <option value="planned">Planned</option>
                            <option value="committed">Committed</option>
                            <option value="paid">Paid</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-destructive hover:bg-destructive/10"
                            onClick={() => handleDeleteExpense(exp.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* EDIT TOTAL LIMIT MODAL */}
      {editingLimit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Update Budget Ceiling</CardTitle>
              <CardDescription>Enter the total maximum spending limit for this event.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium">Total Limit ({currency})</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={limitInput}
                  onChange={(e) => setLimitInput(e.target.value)}
                  className="mt-1"
                />
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingLimit(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveBudgetLimit} disabled={savingLimit}>
                {savingLimit && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />} Save Limit
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* ADD CATEGORY MODAL */}
      {categoryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md">
            <form onSubmit={handleCreateCategory}>
              <CardHeader>
                <CardTitle>Create Budget Category</CardTitle>
                <CardDescription>Add a customized allocation category for your event.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium">Category Name</label>
                  <Input
                    placeholder="e.g. Venue & Catering"
                    value={catName}
                    onChange={(e) => {
                      setCatName(e.target.value);
                      if (!catKey) setCatKey(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_"));
                    }}
                    required
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Category Key (identifier)</label>
                  <Input
                    placeholder="e.g. venue_catering"
                    value={catKey}
                    onChange={(e) => setCatKey(e.target.value)}
                    required
                    className="mt-1 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Planned Allocation ({currency})</label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={catPlanned}
                    onChange={(e) => setCatPlanned(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setCategoryModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={savingCategory}>
                  {savingCategory && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />} Create Category
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {/* ADD EXPENSE MODAL */}
      {expenseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md">
            <form onSubmit={handleCreateExpense}>
              <CardHeader>
                <CardTitle>Record New Expense</CardTitle>
                <CardDescription>Track payments, committed vendor quotes, or planned costs.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium">Category</label>
                  <select
                    value={expCategory}
                    onChange={(e) => setExpCategory(e.target.value)}
                    required
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Select a category...</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium">Description</label>
                  <Input
                    placeholder="e.g. Mandap advance payment"
                    value={expDesc}
                    onChange={(e) => setExpDesc(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Amount ({currency})</label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0.01"
                    placeholder="0.00"
                    value={expAmount}
                    onChange={(e) => setExpAmount(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Status</label>
                  <select
                    value={expStatus}
                    onChange={(e) => setExpStatus(e.target.value as ExpenseStatus)}
                    className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  >
                    <option value="planned">Planned (Estimate / Budgeted)</option>
                    <option value="committed">Committed (Contract Signed / Deposit Due)</option>
                    <option value="paid">Paid (Settled)</option>
                  </select>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setExpenseModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={savingExpense}>
                  {savingExpense && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />} Save Expense
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {/* AI BUDGET ASSISTANT MODAL */}
      {aiModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm">
          <Card className="max-h-[90vh] w-full max-w-2xl overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  <CardTitle>BudgetAI Intelligent Recommender</CardTitle>
                </div>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setAiModalOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>
                Describe your financial constraints, guest scale, and priorities. BudgetAI will propose an optimal
                category distribution tailored to your event.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium">Planning Requirements & Priorities</label>
                <textarea
                  rows={3}
                  className="mt-1 w-full rounded-md border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="e.g. ₹18 lakh budget for 350 guests. Prioritize royal Rajasthani food and hospitality, reduce decor expense."
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                />
              </div>

              {/* Sample prompts */}
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Focus on catering and guest experience, trim decor",
                  "Balanced allocation with emergency buffer",
                  "Destination wedding setup with high transit/stay costs",
                ].map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => setAiPrompt(chip)}
                    className="rounded-full border bg-secondary/50 px-2.5 py-1 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground"
                  >
                    {chip}
                  </button>
                ))}
              </div>

              <div className="flex justify-end">
                <Button onClick={handleGenerateBudgetProposal} disabled={aiGenerating || !aiPrompt.trim()}>
                  {aiGenerating && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                  {aiProposal ? "Regenerate Proposal" : "Generate Recommendations"}
                </Button>
              </div>

              {/* Generated Proposal View */}
              {aiProposal && (
                <div className="mt-4 space-y-4 rounded-lg border bg-muted/20 p-4">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs font-semibold">
                      Proposed Allocation Plan
                    </Badge>
                    <span className="text-xs text-muted-foreground">Base Rev: {aiProposal.base_revision}</span>
                  </div>

                  <p className="text-sm font-medium">{aiProposal.payload.summary}</p>

                  {/* Savings recommendations */}
                  {aiProposal.payload.savings_recommendations.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        Cost Optimization Tips:
                      </div>
                      <ul className="list-inside list-disc text-xs text-muted-foreground">
                        {aiProposal.payload.savings_recommendations.map((tip, i) => (
                          <li key={i}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Categories checkboxes */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold">Select categories to apply:</div>
                    <div className="space-y-2">
                      {aiProposal.payload.proposed_allocations.map((item) => {
                        const checked = selectedCatKeys.has(item.category_key);
                        return (
                          <div
                            key={item.category_key}
                            onClick={() => {
                              const s = new Set(selectedCatKeys);
                              if (checked) s.delete(item.category_key);
                              else s.add(item.category_key);
                              setSelectedCatKeys(s);
                            }}
                            className={`flex cursor-pointer items-start justify-between rounded-md border p-2.5 text-xs transition-colors ${
                              checked ? "border-primary bg-primary/5" : "bg-card"
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => {}}
                                className="mt-0.5 rounded border-primary"
                              />
                              <div>
                                <span className="font-semibold">{item.name}</span>
                                {item.notes && <p className="text-muted-foreground">{item.notes}</p>}
                              </div>
                            </div>
                            <div className="text-right">
                              <span className="font-bold text-foreground">{item.percentage}%</span>
                              <div className="text-muted-foreground">
                                {currency} {Number(item.suggested_amount).toLocaleString("en-IN")}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
            {aiProposal && (
              <CardFooter className="flex justify-between border-t pt-4">
                <Button variant="ghost" onClick={() => setAiModalOpen(false)}>
                  Close
                </Button>
                <Button
                  onClick={handleAcceptBudgetProposal}
                  disabled={aiAccepting || selectedCatKeys.size === 0}
                  className="bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  {aiAccepting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                  Approve & Apply {selectedCatKeys.size} Allocations
                </Button>
              </CardFooter>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
