"use client";

import { useState } from "react";
import { Sparkles, ArrowRight, Plus, Trash2, Calendar, Users, DollarSign, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { adaptiveService } from "../services/adaptive-service";
import type { ChangeProposal, ChangeProposalCreate, FunctionChangeItem } from "../types";

interface ChangeRequestFormProps {
  eventId: string;
  currentRevision: number;
  initialGuestCount?: number;
  initialStartDate?: string;
  initialEndDate?: string;
  initialLocation?: string;
  onProposalCreated: (proposal: ChangeProposal) => void;
}

export function ChangeRequestForm({
  eventId,
  currentRevision,
  initialGuestCount,
  initialStartDate,
  initialEndDate,
  initialLocation,
  onProposalCreated,
}: ChangeRequestFormProps) {
  const [prompt, setPrompt] = useState("");
  const [interpreting, setInterpreting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Structured form state
  const [requestText, setRequestText] = useState("");
  const [guestCount, setGuestCount] = useState<string>(initialGuestCount ? String(initialGuestCount) : "");
  const [startAt, setStartAt] = useState<string>(initialStartDate ? initialStartDate.slice(0, 16) : "");
  const [endAt, setEndAt] = useState<string>(initialEndDate ? initialEndDate.slice(0, 16) : "");
  const [locationName, setLocationName] = useState<string>(initialLocation || "");
  const [budgetLimit, setBudgetLimit] = useState<string>("");
  const [functionChanges, setFunctionChanges] = useState<FunctionChangeItem[]>([]);

  const handleInterpret = async () => {
    if (!prompt.trim()) return;
    setInterpreting(true);
    setError(null);
    try {
      const res = await adaptiveService.interpretPrompt(eventId, prompt.trim());
      setRequestText(res.candidate_request.request_text);

      const evChg = res.candidate_request.event_changes;
      if (evChg) {
        if (evChg.expected_guest_count) setGuestCount(String(evChg.expected_guest_count));
        if (evChg.start_at) setStartAt(evChg.start_at.slice(0, 16));
        if (evChg.end_at) setEndAt(evChg.end_at.slice(0, 16));
        if (evChg.location_name) setLocationName(evChg.location_name);
      }

      const bChg = res.candidate_request.budget_changes;
      if (bChg && bChg.total_limit) {
        setBudgetLimit(String(bChg.total_limit));
      }

      if (res.candidate_request.function_changes && res.candidate_request.function_changes.length > 0) {
        setFunctionChanges(res.candidate_request.function_changes);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to interpret prompt.";
      setError(msg);
      if (!requestText) setRequestText(prompt.trim());
    } finally {
      setInterpreting(false);
    }
  };

  const handleAddFunctionChange = () => {
    setFunctionChanges((prev) => [
      ...prev,
      {
        action: "add",
        name: "",
        function_type: "ceremony",
      },
    ]);
  };

  const handleRemoveFunctionChange = (index: number) => {
    setFunctionChanges((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalRequestText = requestText.trim() || prompt.trim();
    if (!finalRequestText) {
      setError("Please describe the celebration change.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload: ChangeProposalCreate = {
      base_revision: currentRevision,
      request_text: finalRequestText,
      event_changes:
        guestCount || startAt || endAt || locationName
          ? {
              expected_guest_count: guestCount ? parseInt(guestCount, 10) : undefined,
              start_at: startAt ? new Date(startAt).toISOString() : undefined,
              end_at: endAt ? new Date(endAt).toISOString() : undefined,
              location_name: locationName.trim() || undefined,
            }
          : undefined,
      budget_changes: budgetLimit ? { total_limit: budgetLimit } : undefined,
      function_changes: functionChanges.filter((f) => f.name && f.name.trim().length > 0),
    };

    try {
      const proposal = await adaptiveService.createProposal(eventId, payload);
      onProposalCreated(proposal);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate change proposal.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-lg font-semibold tracking-tight text-foreground">
          Propose Celebration Requirement Change
        </h3>
        <p className="text-sm text-muted-foreground">
          Describe planned adjustments in plain language or configure structured fields. Our deterministic engine
          calculates the ripple effect across BudgetAI, TimelineAI, VendorConnect, and GiftCircle.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {error}
        </div>
      )}

      {/* Natural Language Prompt Box */}
      <div className="mb-6 rounded-lg border bg-muted/30 p-4">
        <Label htmlFor="nl-prompt" className="text-xs font-semibold uppercase text-muted-foreground">
          Step 1: Express change in plain English
        </Label>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row">
          <Input
            id="nl-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Express planned change in plain English..."
            className="flex-1"
            disabled={interpreting || submitting}
          />
          <Button
            type="button"
            variant="secondary"
            onClick={handleInterpret}
            disabled={!prompt.trim() || interpreting || submitting}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4 text-primary" />
            {interpreting ? "Interpreting..." : "AI Interpret"}
          </Button>
        </div>
      </div>

      {/* Structured Fields Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="request-text">Proposal Title / Summary Description</Label>
          <Input
            id="request-text"
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            placeholder="e.g. Increase guest count and add Sangeet ceremony"
            required
            disabled={submitting}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="guest-count" className="flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-muted-foreground" />
              Expected Guest Count
            </Label>
            <Input
              id="guest-count"
              type="number"
              min="1"
              max="100000"
              value={guestCount}
              onChange={(e) => setGuestCount(e.target.value)}
              placeholder="e.g. 350"
              disabled={submitting}
            />
          </div>

          <div>
            <Label htmlFor="budget-limit" className="flex items-center gap-1.5">
              <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
              Budget Total Limit
            </Label>
            <Input
              id="budget-limit"
              type="number"
              step="0.01"
              value={budgetLimit}
              onChange={(e) => setBudgetLimit(e.target.value)}
              placeholder="e.g. 2500000"
              disabled={submitting}
            />
          </div>

          <div>
            <Label htmlFor="start-at" className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
              Start Date & Time
            </Label>
            <Input
              id="start-at"
              type="datetime-local"
              value={startAt}
              onChange={(e) => setStartAt(e.target.value)}
              disabled={submitting}
            />
          </div>

          <div>
            <Label htmlFor="end-at" className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
              End Date & Time
            </Label>
            <Input
              id="end-at"
              type="datetime-local"
              value={endAt}
              onChange={(e) => setEndAt(e.target.value)}
              disabled={submitting}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="location-name" className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
            Location / Venue Name
          </Label>
          <Input
            id="location-name"
            value={locationName}
            onChange={(e) => setLocationName(e.target.value)}
            placeholder="e.g. Rambagh Palace, Jaipur"
            disabled={submitting}
          />
        </div>

        {/* Function Modifications */}
        <div className="pt-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs font-semibold uppercase text-muted-foreground">
              Celebration Function Changes
            </Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddFunctionChange}
              className="h-7 gap-1 text-xs"
            >
              <Plus className="h-3 w-3" /> Add Function
            </Button>
          </div>

          {functionChanges.length > 0 && (
            <div className="mt-2 space-y-2">
              {functionChanges.map((fc, idx) => (
                <div key={idx} className="flex items-center gap-2 rounded-lg border bg-muted/20 p-2">
                  <select
                    value={fc.action}
                    onChange={(e) => {
                      const action = e.target.value as "add" | "update" | "archive";
                      setFunctionChanges((prev) =>
                        prev.map((item, i) => (i === idx ? { ...item, action } : item))
                      );
                    }}
                    className="h-8 rounded-md border bg-background px-2 text-xs"
                  >
                    <option value="add">Add</option>
                    <option value="update">Update</option>
                    <option value="archive">Archive</option>
                  </select>
                  <Input
                    value={fc.name || ""}
                    onChange={(e) => {
                      const name = e.target.value;
                      setFunctionChanges((prev) =>
                        prev.map((item, i) => (i === idx ? { ...item, name } : item))
                      );
                    }}
                    placeholder="Function name (e.g. Sangeet & Mehendi)"
                    className="h-8 text-xs"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveFunctionChange(idx)}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={submitting} className="gap-2">
            {submitting ? "Analyzing Downstream Impacts..." : "Analyze Downstream Impacts"}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
