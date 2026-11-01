"use client";

import { useCallback, useEffect, useState } from "react";
import { History, Sparkles, Sliders } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChangeRequestForm } from "./change-request-form";
import { ImpactPreviewView } from "./impact-preview-view";
import { ProposalDetailDialog } from "./proposal-detail-dialog";
import { adaptiveService } from "../services/adaptive-service";
import type { ChangeProposal } from "../types";

interface AdaptiveDashboardProps {
  eventId: string;
  eventTitle: string;
  currentRevision: number;
  expectedGuestCount?: number;
  startAt?: string;
  endAt?: string;
  locationName?: string;
  myRole: string;
}

export function AdaptiveDashboard({
  eventId,
  eventTitle,
  currentRevision,
  expectedGuestCount,
  startAt,
  endAt,
  locationName,
  myRole,
}: AdaptiveDashboardProps) {
  const isOwner = myRole === "owner";
  const [proposals, setProposals] = useState<ChangeProposal[]>([]);
  const [activeProposal, setActiveProposal] = useState<ChangeProposal | null>(null);
  const [inspectProposal, setInspectProposal] = useState<ChangeProposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const loadProposals = useCallback(async () => {
    setLoading(true);
    try {
      const list = await adaptiveService.listProposals(eventId);
      setProposals(list);

      // Default active proposal to the latest proposed item if any
      const pending = list.find((p) => p.status === "proposed");
      if (pending && !activeProposal) {
        setActiveProposal(pending);
      }
    } catch (err) {
      console.error("Failed to load change proposals", err);
    } finally {
      setLoading(false);
    }
  }, [eventId, activeProposal]);

  useEffect(() => {
    loadProposals();
  }, [loadProposals]);

  const handleProposalCreated = (newProposal: ChangeProposal) => {
    setActiveProposal(newProposal);
    setProposals((prev) => [newProposal, ...prev.filter((p) => p.id !== newProposal.id)]);
  };

  const handleProposalUpdated = (updated: ChangeProposal) => {
    if (activeProposal?.id === updated.id) {
      setActiveProposal(updated);
    }
    setProposals((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    loadProposals();
  };

  const filteredProposals = proposals.filter((p) => {
    if (statusFilter === "all") return true;
    return p.status === statusFilter;
  });

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col justify-between gap-4 rounded-xl border bg-gradient-to-r from-card via-muted/40 to-card p-6 shadow-sm sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Adaptive Planning Engine
            </h2>
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary">
              Phase 6
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Intelligent cross-module decision and replanning system for {eventTitle}.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-lg border bg-background/80 px-4 py-2 text-right">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Event Revision</div>
            <div className="text-lg font-bold text-foreground">rev #{currentRevision}</div>
          </div>
        </div>
      </div>

      {/* Active Proposal View (if any) */}
      {activeProposal && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              <Sparkles className="h-4 w-4 text-primary" /> Active Change Proposal
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setActiveProposal(null)}
              className="h-7 text-xs text-muted-foreground"
            >
              Close Preview
            </Button>
          </div>
          <ImpactPreviewView
            proposal={activeProposal}
            isOwner={isOwner}
            onProposalUpdated={handleProposalUpdated}
            onDismiss={() => setActiveProposal(null)}
          />
        </div>
      )}

      {/* Main Grid: Change Request Creator + History */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: Form */}
        <div className="lg:col-span-7">
          <ChangeRequestForm
            eventId={eventId}
            currentRevision={currentRevision}
            initialGuestCount={expectedGuestCount}
            initialStartDate={startAt}
            initialEndDate={endAt}
            initialLocation={locationName}
            onProposalCreated={handleProposalCreated}
          />
        </div>

        {/* Right Column: Proposal History */}
        <div className="space-y-4 lg:col-span-5">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
              <History className="h-4 w-4 text-muted-foreground" /> Proposal History
            </h3>
            <div className="flex gap-1 text-xs">
              {["all", "proposed", "accepted", "stale"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setStatusFilter(filter)}
                  className={`rounded-md px-2 py-1 capitalize transition-colors ${
                    statusFilter === filter
                      ? "bg-primary text-primary-foreground font-medium"
                      : "bg-muted/50 text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="rounded-xl border bg-card p-8 text-center text-xs text-muted-foreground">
              Loading change history...
            </div>
          ) : filteredProposals.length === 0 ? (
            <div className="rounded-xl border bg-card p-8 text-center text-xs text-muted-foreground">
              No change proposals found matching &quot;{statusFilter}&quot;.
            </div>
          ) : (
            <div className="space-y-3">
              {filteredProposals.map((prop) => (
                <div
                  key={prop.id}
                  onClick={() => setInspectProposal(prop)}
                  className="group flex cursor-pointer items-start justify-between rounded-xl border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-sm"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-foreground group-hover:text-primary">
                        {prop.request_text}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] uppercase font-semibold ${
                          prop.status === "accepted"
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-600"
                            : prop.status === "proposed"
                              ? "border-primary/40 bg-primary/10 text-primary"
                              : "border-muted-foreground/30 text-muted-foreground"
                        }`}
                      >
                        {prop.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Base rev #{prop.base_revision} • {new Date(prop.created_at).toLocaleDateString()}
                    </p>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {prop.impact_result.affected_modules.map((m) => (
                        <span
                          key={m}
                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] capitalize text-muted-foreground"
                        >
                          {m.replace("_", " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Sliders className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal Dialog for Historical Proposal Inspection */}
      <ProposalDetailDialog
        proposal={inspectProposal}
        isOpen={Boolean(inspectProposal)}
        isOwner={isOwner}
        onClose={() => setInspectProposal(null)}
        onProposalUpdated={handleProposalUpdated}
      />
    </div>
  );
}
