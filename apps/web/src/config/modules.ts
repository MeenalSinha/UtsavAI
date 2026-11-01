/** Workspace module navigation. Only Overview is implemented in Phase 1. */
export interface WorkspaceModule {
  key: string;
  label: string;
  description: string;
  available: boolean;
  phase: string;
}

export const WORKSPACE_MODULES: readonly WorkspaceModule[] = [
  { key: "overview", label: "Overview", description: "Event details and status", available: true, phase: "Phase 1" },
  { key: "planai", label: "PlanAI", description: "Personalised event planning and recommendations", available: false, phase: "Phase 2" },
  { key: "budgetai", label: "BudgetAI", description: "Budget allocation and expense tracking", available: false, phase: "Phase 3" },
  { key: "timelineai", label: "TimelineAI", description: "Schedule, deadlines and tasks", available: false, phase: "Phase 3" },
  { key: "vendorconnect", label: "VendorConnect", description: "Vendors, quotations and bookings", available: false, phase: "Phase 4" },
  { key: "giftcircle", label: "GiftCircle", description: "Shareable gift registries and group gifting", available: false, phase: "Phase 5" },
] as const;
