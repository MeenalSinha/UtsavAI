"use client";

import { useState } from "react";
import { Check, Copy, Link as LinkIcon, RefreshCw, Trash2 } from "lucide-react";

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
import type { GiftRegistryShareLinkResponse, GiftRegistryShareLinkStatus } from "../types";

interface ShareLinkDialogProps {
  eventId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  status: GiftRegistryShareLinkStatus | null;
  onStatusChange: (status: GiftRegistryShareLinkStatus) => void;
}

export function ShareLinkDialog({
  eventId,
  open,
  onOpenChange,
  status,
  onStatusChange,
}: ShareLinkDialogProps) {
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeUrl, setActiveUrl] = useState<string | null>(status?.share_url || null);

  const handleCopy = async () => {
    if (!activeUrl) return;
    try {
      await navigator.clipboard.writeText(activeUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy link to clipboard.");
    }
  };

  const handleGenerateOrRotate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res: GiftRegistryShareLinkResponse = await giftService.rotateShareLink(eventId);
      setActiveUrl(res.share_url);
      onStatusChange({
        has_active_link: true,
        share_url: res.share_url,
        expires_at: res.expires_at,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to generate share link.");
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!confirm("Are you sure you want to revoke this link? Anyone with the existing link will immediately lose access.")) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await giftService.revokeShareLink(eventId);
      setActiveUrl(null);
      onStatusChange({
        has_active_link: false,
        share_url: null,
        expires_at: null,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to revoke share link.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5 text-primary" />
            Registry Public Share Link
          </DialogTitle>
          <DialogDescription>
            Share this link with wedding guests so they can view your wishlist, reserve gifts, or pledge to group gifts without needing to sign up.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
            {error}
          </div>
        )}

        <div className="space-y-4 py-3">
          {activeUrl ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="share-link-input">Guest Access URL</Label>
                <div className="flex gap-2">
                  <Input
                    id="share-link-input"
                    value={activeUrl}
                    readOnly
                    className="font-mono text-xs select-all"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleCopy}
                    title="Copy Link"
                  >
                    {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Security note: Only a cryptographic hash of this token is stored. Rotating this link will permanently invalidate earlier shared URLs.
                </p>
              </div>

              <div className="flex items-center justify-between pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateOrRotate}
                  disabled={loading}
                >
                  <RefreshCw className="mr-2 h-3.5 w-3.5" />
                  Rotate Link
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={handleRevoke}
                  disabled={loading}
                >
                  <Trash2 className="mr-2 h-3.5 w-3.5" />
                  Revoke Link
                </Button>
              </div>
            </>
          ) : (
            <div className="rounded-lg border border-dashed p-6 text-center">
              <LinkIcon className="mx-auto h-8 w-8 text-muted-foreground/60" />
              <h4 className="mt-2 text-sm font-semibold">No active public link</h4>
              <p className="mt-1 text-xs text-muted-foreground">
                Generate a secure, unguessable link to share your registry with your guests.
              </p>
              <Button
                type="button"
                className="mt-4"
                onClick={handleGenerateOrRotate}
                disabled={loading}
              >
                Generate Share Link
              </Button>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
