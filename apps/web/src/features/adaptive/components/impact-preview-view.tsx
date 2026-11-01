"use client";

import { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  CheckSquare,
  Clock,
  DollarSign,
  Gift,
  Info,
  ListTodo,
  ShieldAlert,
  Sparkles,
  Users,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { adaptiveService } from "../services/adaptive-service";
import type { ChangeProposal } from "../types";

interface ImpactPreviewViewProps {
  proposal: ChangeProposal;
  isOwner: boolean;
  onProposalUpdated: (updated: ChangeProposal) => void;
  onDismiss?: () => void;
}

export function ImpactPreviewView({
  proposal,
  isOwner,
  onProposalUpdated,
  onDismiss,
}: ImpactPreviewViewProps) {
  const [selectedOptions, setSelectedOptions] = useState<string[]>(
    proposal.impact_result.suggested_options
      .filter((opt) => opt.selected_by_default)
      .map((opt) => opt.id)
  );
  const [applying, setApplying] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const toggleOption = (id: string) => {
    setSelectedOptions((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleAccept = async () => {
    if (!isOwner) {
      setActionError("Only the event owner can approve and atomically apply changes.");
      return;
    }
    setApplying(true);
    setActionError(null);
    try {
      const updated = await adaptiveService.acceptProposal(proposal.event_id, proposal.id, {
        selected_option_ids: selectedOptions,
      });
      onProposalUpdated(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to accept proposal.";
      setActionError(msg);
    } finally {
      setApplying(false);
    }
  };

  const handleReject = async () => {
    setRejecting(true);
    setActionError(null);
    try {
      const updated = await adaptiveService.rejectProposal(proposal.event_id, proposal.id, {
        reason: "Rejected by event host",
      });
      onProposalUpdated(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to reject proposal.";
      setActionError(msg);
    } finally {
      setRejecting(false);
    }
  };

  const severityBadgeClass = {
    critical: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30",
    high: "bg-orange-500/15 text-orange-700 dark:text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/30",
    low: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  }[proposal.impact_result.severity];

  const moduleIconMap: Record<string, React.ReactNode> = {
    event: <Users className="h-4 w-4 text-blue-500" />,
    plan_ai: <Sparkles className="h-4 w-4 text-purple-500" />,
    budget: <DollarSign className="h-4 w-4 text-emerald-500" />,
    timeline: <Clock className="h-4 w-4 text-amber-500" />,
    vendors: <ListTodo className="h-4 w-4 text-indigo-500" />,
    giftcircle: <Gift className="h-4 w-4 text-rose-500" />,
  };

  return (
    <div className="space-y-6 rounded-xl border bg-card p-6 shadow-sm">
      {/* Header & Status Banner */}
      <div className="flex flex-col justify-between gap-4 border-b pb-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-bold tracking-tight text-foreground">
              {proposal.request_text}
            </h3>
            <Badge variant="outline" className={`capitalize font-semibold ${severityBadgeClass}`}>
              {proposal.impact_result.severity} Impact
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Proposal ID: <span className="font-mono">{proposal.id.slice(0, 8)}</span> • Base Revision:{" "}
            <span className="font-semibold">{proposal.base_revision}</span> • Status:{" "}
            <span className="font-semibold uppercase">{proposal.status}</span>
          </p>
        </div>

        {proposal.status === "accepted" && (
          <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4" />
            Accepted (Applied at Revision {proposal.accepted_revision})
          </div>
        )}

        {proposal.status === "rejected" && (
          <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-1.5 text-xs font-semibold text-muted-foreground">
            <XCircle className="h-4 w-4" /> Rejected
          </div>
        )}

        {proposal.status === "stale" && (
          <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-700 dark:text-amber-400">
            <AlertTriangle className="h-4 w-4" /> Stale (Event Revision Advanced)
          </div>
        )}
      </div>

      {actionError && (
        <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {actionError}
        </div>
      )}

      {/* Affected Modules Summary */}
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Affected Event Modules ({proposal.impact_result.affected_modules.length})
        </h4>
        <div className="flex flex-wrap gap-2">
          {proposal.impact_result.affected_modules.map((m) => (
            <div
              key={m}
              className="flex items-center gap-1.5 rounded-lg border bg-muted/40 px-3 py-1.5 text-xs font-medium text-foreground"
            >
              {moduleIconMap[m] || <Info className="h-4 w-4 text-muted-foreground" />}
              <span className="capitalize">{m.replace("_", " ")}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Warnings & Considerations */}
      {proposal.impact_result.warnings.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Key Considerations & Warnings
          </h4>
          <div className="space-y-2">
            {proposal.impact_result.warnings.map((w, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-lg border border-border/80 bg-muted/20 p-3 text-sm"
              >
                {w.severity === "critical" || w.severity === "high" ? (
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                ) : (
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                )}
                <div>
                  <div className="font-semibold text-foreground">{w.message}</div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">Action:</span> {w.recommended_action}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Impact Calculations */}
      {proposal.impact_result.calculations.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Deterministic Impact Calculations
          </h4>
          <div className="overflow-hidden rounded-lg border">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Metric</th>
                  <th className="px-3 py-2 font-medium">Before</th>
                  <th className="px-3 py-2 font-medium">After</th>
                  <th className="px-3 py-2 font-medium">Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {proposal.impact_result.calculations.map((calc, i) => (
                  <tr key={i} className="hover:bg-muted/30">
                    <td className="px-3 py-2 font-medium text-foreground">{calc.metric}</td>
                    <td className="px-3 py-2 text-muted-foreground">{calc.before_value}</td>
                    <td className="px-3 py-2 font-medium text-foreground">{calc.after_value}</td>
                    <td className="px-3 py-2 font-bold text-primary">{calc.delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Advisory AI Explanation */}
      {proposal.ai_explanation && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <Sparkles className="h-4 w-4" /> Advisory Analysis & Guidance
          </div>
          <div className="prose prose-sm dark:prose-invert mt-2 max-w-none text-xs text-foreground/90 whitespace-pre-line">
            {proposal.ai_explanation}
          </div>
        </div>
      )}

      {/* Suggested Secondary Options Checkboxes */}
      {proposal.impact_result.suggested_options.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Recommended Mitigations & Secondary Adjustments
          </h4>
          <div className="space-y-2">
            {proposal.impact_result.suggested_options.map((opt) => {
              const isChecked = selectedOptions.includes(opt.id);
              const disabled = proposal.status !== "proposed";
              return (
                <label
                  key={opt.id}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors ${
                    isChecked ? "border-primary/40 bg-primary/5" : "bg-muted/20 hover:bg-muted/30"
                  } ${disabled ? "cursor-not-allowed opacity-75" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    disabled={disabled}
                    onChange={() => toggleOption(opt.id)}
                    className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <div className="flex-1">
                    <div className="font-semibold text-foreground">{opt.title}</div>
                    <div className="text-xs text-muted-foreground">{opt.description}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Affected Records Detail */}
      {proposal.impact_result.affected_records.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Affected Records ({proposal.impact_result.affected_records.length})
          </h4>
          <div className="max-h-48 overflow-y-auto rounded-lg border text-xs">
            <table className="w-full text-left">
              <thead className="sticky top-0 bg-muted/80 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Module</th>
                  <th className="px-3 py-2 font-medium">Entity</th>
                  <th className="px-3 py-2 font-medium">Nature</th>
                  <th className="px-3 py-2 font-medium">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {proposal.impact_result.affected_records.map((r, i) => (
                  <tr key={i} className="hover:bg-muted/30">
                    <td className="px-3 py-1.5 font-medium capitalize text-foreground">{r.module}</td>
                    <td className="px-3 py-1.5 text-foreground">{r.entity_name}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{r.change_nature}</td>
                    <td className="px-3 py-1.5 text-muted-foreground">{r.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Decision Actions Bar */}
      <div className="flex flex-col-reverse justify-end gap-2 border-t pt-4 sm:flex-row sm:items-center">
        {onDismiss && (
          <Button variant="ghost" onClick={onDismiss} disabled={applying || rejecting}>
            Dismiss
          </Button>
        )}

        {proposal.status === "proposed" && (
          <>
            <Button
              variant="outline"
              onClick={handleReject}
              disabled={applying || rejecting}
              className="text-destructive hover:bg-destructive/10"
            >
              {rejecting ? "Rejecting..." : "Reject Proposal"}
            </Button>
            <Button
              onClick={handleAccept}
              disabled={applying || rejecting || !isOwner}
              className="gap-2"
            >
              <CheckSquare className="h-4 w-4" />
              {applying ? "Applying Atomically..." : "Approve & Apply Changes"}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
