"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { giftService } from "../services/gift-service";
import type { GiftContributionDto, VerificationMethod } from "../types";

interface VerifyContributionDialogProps {
  eventId: string;
  contribution: GiftContributionDto | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function VerifyContributionDialog({
  eventId,
  contribution,
  open,
  onOpenChange,
  onSuccess,
}: VerifyContributionDialogProps) {
  const [method, setMethod] = useState<VerificationMethod>("offline_cash");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!contribution) return null;

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await giftService.verifyContribution(eventId, contribution.id, {
        verification_method: method,
        verification_notes: notes.trim() || null,
      });
      onSuccess();
      onOpenChange(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to verify contribution.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[450px]">
        <form onSubmit={handleVerify}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              Verify Offline Contribution
            </DialogTitle>
            <DialogDescription>
              Confirm receipt of this guest pledge on your celebration day or via direct bank settlement.
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="mt-3 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
              {error}
            </div>
          )}

          <div className="space-y-4 py-4">
            <div className="rounded-lg bg-muted/60 p-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Guest:</span>
                <span className="font-semibold">{contribution.guest_alias || "Anonymous Guest"}</span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-muted-foreground">Pledged Amount:</span>
                <span className="font-bold text-primary">₹{Number(contribution.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="verify-method">Receipt / Settlement Method *</Label>
              <select
                id="verify-method"
                value={method}
                onChange={(e) => setMethod(e.target.value as VerificationMethod)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="offline_cash">Cash envelope / In-person</option>
                <option value="upi_direct">Direct UPI settlement</option>
                <option value="bank_transfer">Bank transfer / NEFT / IMPS</option>
                <option value="gift_card">Store / Brand Gift Card</option>
                <option value="other">Other offline receipt</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="verify-notes">Host Notes (Optional)</Label>
              <Input
                id="verify-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Received at reception counter, Envelope #12"
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="bg-emerald-600 hover:bg-emerald-700">
              {loading ? "Confirming..." : "Confirm Receipt"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
