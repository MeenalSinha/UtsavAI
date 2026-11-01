"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ImpactPreviewView } from "./impact-preview-view";
import type { ChangeProposal } from "../types";

interface ProposalDetailDialogProps {
  proposal: ChangeProposal | null;
  isOpen: boolean;
  isOwner: boolean;
  onClose: () => void;
  onProposalUpdated: (updated: ChangeProposal) => void;
}

export function ProposalDetailDialog({
  proposal,
  isOpen,
  isOwner,
  onClose,
  onProposalUpdated,
}: ProposalDetailDialogProps) {
  if (!proposal) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto p-6">
        <DialogHeader>
          <DialogTitle>Change Proposal Review</DialogTitle>
        </DialogHeader>
        <ImpactPreviewView
          proposal={proposal}
          isOwner={isOwner}
          onProposalUpdated={(updated) => {
            onProposalUpdated(updated);
            onClose();
          }}
          onDismiss={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
