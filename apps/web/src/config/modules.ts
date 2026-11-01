/** Workspace module navigation for Phase 1 & 2. */
export interface WorkspaceModule {
  key: string;
  label: string;
  description: string;
  available: boolean;
  phase: string;
}

export const WORKSPACE_MODULES: readonly WorkspaceModule[] = [
  { key: "overview", label: "Overview", description: "Event details and status", available: true, phase: "Phase 1" },
  { key: "planai", label: "PlanAI", description: "Personalised event planning and recommendations", available: true, phase: "Phase 2" },
  { key: "preferences", label: "Preferences", description: "Cultural, style and accessibility requirements", available: true, phase: "Phase 2" },
  { key: "functions", label: "Functions", description: "Ceremonies, schedules and venues", available: true, phase: "Phase 2" },
  { key: "budgetai", label: "BudgetAI", description: "Budget allocation and expense tracking", available: true, phase: "Phase 3" },
  { key: "timelineai", label: "TimelineAI", description: "Schedule, deadlines and tasks", available: true, phase: "Phase 3" },
  { key: "vendorconnect", label: "VendorConnect", description: "Vendors, quotations and bookings", available: true, phase: "Phase 4" },
  { key: "giftcircle", label: "GiftCircle", description: "Shareable gift registries and group gifting", available: true, phase: "Phase 5" },
  { key: "adaptiveplan", label: "Adaptive Plan", description: "Dynamic replanning and live updates", available: false, phase: "Phase 6" },
] as const;
