import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

type Tone = "error" | "success" | "info";
const tones: Record<Tone, { cls: string; Icon: typeof Info }> = {
  error: { cls: "border-destructive/40 bg-red-50 text-red-900", Icon: AlertCircle },
  success: { cls: "border-emerald-300 bg-emerald-50 text-emerald-900", Icon: CheckCircle2 },
  info: { cls: "border-border bg-secondary text-secondary-foreground", Icon: Info },
};

export function Alert({ tone = "info", className, children, ...props }: React.HTMLAttributes<HTMLDivElement> & { tone?: Tone }) {
  const { cls, Icon } = tones[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={cn("flex gap-3 rounded-md border p-3 text-sm", cls, className)} {...props}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div>{children}</div>
    </div>
  );
}
