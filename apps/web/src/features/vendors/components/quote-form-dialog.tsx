"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { QuoteStatus, VendorQuoteCreatePayload, VendorQuoteDto, VendorQuoteUpdatePayload } from "../types";

interface QuoteFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vendorName: string;
  currency?: string;
  quote?: VendorQuoteDto | null;
  onSubmit: (payload: VendorQuoteCreatePayload | VendorQuoteUpdatePayload) => Promise<void>;
}

export function QuoteFormDialog({
  open,
  onOpenChange,
  vendorName,
  currency = "INR",
  quote,
  onSubmit,
}: QuoteFormDialogProps) {
  const [amount, setAmount] = useState(quote?.amount || "");
  const [scopeSummary, setScopeSummary] = useState(quote?.scope_summary || "");
  const [validUntil, setValidUntil] = useState(quote?.valid_until || "");
  const [notes, setNotes] = useState(quote?.notes || "");
  const [status, setStatus] = useState<QuoteStatus>(quote?.status || "received");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount < 0) {
      setError("Please enter a valid non-negative quotation amount.");
      return;
    }
    if (!scopeSummary.trim()) {
      setError("Scope summary is required to compare deliverables.");
      return;
    }

    setSubmitting(true);
    try {
      if (quote) {
        await onSubmit({
          amount: parsedAmount.toFixed(2),
          currency,
          scope_summary: scopeSummary.trim(),
          valid_until: validUntil || null,
          notes: notes.trim() || null,
          status,
        });
      } else {
        await onSubmit({
          amount: parsedAmount.toFixed(2),
          currency,
          scope_summary: scopeSummary.trim(),
          valid_until: validUntil || null,
          notes: notes.trim() || null,
        });
      }
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save quotation.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{quote ? "Edit Quotation" : "Record Vendor Quotation"}</DialogTitle>
          <DialogDescription>
            {quote
              ? `Update quotation proposal from ${vendorName}.`
              : `Record an official quote received from ${vendorName} for side-by-side comparison.`}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="quote-amount">Quoted Amount ({currency}) *</Label>
              <Input
                id="quote-amount"
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="e.g. 450000.00"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="valid-until">Offer Valid Until</Label>
              <Input
                id="valid-until"
                type="date"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="scope-summary">Deliverables & Scope Summary *</Label>
            <Textarea
              id="scope-summary"
              value={scopeSummary}
              onChange={(e) => setScopeSummary(e.target.value)}
              placeholder="e.g. Buffet dinner for 300 guests including live chaat counter, 4 main courses, dessert bar, cutlery & service staff."
              rows={3}
              required
            />
            <p className="text-xs text-muted-foreground">
              Tip: Mention guest count or key deliverables to help the system detect scope differences.
            </p>
          </div>

          {quote && (
            <div className="space-y-1.5">
              <Label htmlFor="quote-status">Quotation Decision Status</Label>
              <select
                id="quote-status"
                value={status}
                onChange={(e) => setStatus(e.target.value as QuoteStatus)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="received">Received (Under review)</option>
                <option value="shortlisted">Shortlisted (In consideration)</option>
                <option value="accepted">Accepted (Selected proposal)</option>
                <option value="rejected">Rejected (Not accepted)</option>
                <option value="expired">Expired (Validity passed)</option>
              </select>
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="quote-notes">Private Host Notes</Label>
            <Textarea
              id="quote-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. 50% advance required on booking, balance on event day."
              rows={2}
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : quote ? "Update Quote" : "Save Quotation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
