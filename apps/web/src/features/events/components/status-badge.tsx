import { Badge } from "@/components/ui/badge";
import type { EventStatus } from "@/types/api";

const LABELS: Record<EventStatus, { label: string; variant: "muted" | "warning" | "success" | "secondary" }> = {
  draft: { label: "Draft", variant: "muted" },
  planning: { label: "Planning", variant: "warning" },
  completed: { label: "Completed", variant: "success" },
  archived: { label: "Archived", variant: "secondary" },
};

export function StatusBadge({ status }: { status: EventStatus }) {
  const { label, variant } = LABELS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function statusLabel(status: EventStatus): string {
  return LABELS[status].label;
}
