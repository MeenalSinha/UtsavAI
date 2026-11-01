"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  ExternalLink,
  FileText,
  Mail,
  Phone,
  Plus,
  Receipt,
  User,
} from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { routes } from "@/config/routes";
import { vendorService } from "../services/vendor-service";
import type { QuoteStatus, VendorDetailDto, VendorDto, VendorQuoteCreatePayload, VendorQuoteDto, VendorQuoteUpdatePayload } from "../types";
import { QuoteFormDialog } from "./quote-form-dialog";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

interface VendorDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  eventId: string;
  vendor: VendorDto | null;
  onVendorUpdated: () => void;
  onEditVendor: (vendor: VendorDto) => void;
  onArchiveVendor: (vendor: VendorDto) => void;
}

export function VendorDetailDialog({
  open,
  onOpenChange,
  eventId,
  vendor,
  onVendorUpdated,
  onEditVendor,
  onArchiveVendor,
}: VendorDetailDialogProps) {
  const [activeTab, setActiveTab] = useState<"quotes" | "expenses" | "overview">("quotes");
  const [details, setDetails] = useState<VendorDetailDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [quoteDialogOpen, setQuoteDialogOpen] = useState(false);
  const [editingQuote, setEditingQuote] = useState<VendorQuoteDto | null>(null);

  useEffect(() => {
    if (open && vendor) {
      setLoading(true);
      vendorService
        .getVendor(eventId, vendor.id)
        .then(setDetails)
        .catch((err) => console.error("Failed to load vendor details", err))
        .finally(() => setLoading(false));
    } else {
      setDetails(null);
    }
  }, [open, vendor, eventId]);

  if (!vendor) return null;

  const handleSaveQuote = async (payload: VendorQuoteCreatePayload | VendorQuoteUpdatePayload) => {
    if (editingQuote) {
      await vendorService.updateQuote(eventId, vendor.id, editingQuote.id, payload as VendorQuoteUpdatePayload);
    } else {
      await vendorService.createQuote(eventId, vendor.id, payload as VendorQuoteCreatePayload);
    }
    const refreshed = await vendorService.getVendor(eventId, vendor.id);
    setDetails(refreshed);
    onVendorUpdated();
  };

  const handleUpdateQuoteStatus = async (quote: VendorQuoteDto, newStatus: QuoteStatus) => {
    await vendorService.updateQuote(eventId, vendor.id, quote.id, { status: newStatus });
    const refreshed = await vendorService.getVendor(eventId, vendor.id);
    setDetails(refreshed);
    onVendorUpdated();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "booked":
        return <Badge className="bg-emerald-600 text-white hover:bg-emerald-700">Booked</Badge>;
      case "shortlisted":
        return <Badge className="bg-purple-600 text-white hover:bg-purple-700">Shortlisted</Badge>;
      case "quoted":
        return <Badge className="bg-blue-600 text-white hover:bg-blue-700">Quoted</Badge>;
      case "contacted":
        return <Badge variant="outline" className="text-amber-600 border-amber-300">Contacted</Badge>;
      case "declined":
        return <Badge variant="muted" className="text-destructive border-destructive/20 bg-destructive/10">Declined</Badge>;
      default:
        return <Badge variant="secondary">Identified</Badge>;
    }
  };

  const getQuoteBadge = (status: string) => {
    switch (status) {
      case "accepted":
        return <Badge className="bg-emerald-600 text-white">Accepted</Badge>;
      case "shortlisted":
        return <Badge className="bg-purple-600 text-white">Shortlisted</Badge>;
      case "rejected":
        return <Badge variant="muted" className="text-destructive border-destructive/20 bg-destructive/10">Rejected</Badge>;
      case "expired":
        return <Badge variant="outline" className="text-muted-foreground border-border">Expired</Badge>;
      default:
        return <Badge variant="outline" className="text-blue-600 border-blue-200">Received</Badge>;
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <div className="flex flex-wrap items-center justify-between gap-2 pr-6">
              <div>
                <DialogTitle className="text-2xl font-serif text-primary">{vendor.name}</DialogTitle>
                <DialogDescription className="mt-1 flex items-center gap-2">
                  <span className="font-medium text-foreground">{vendor.category}</span>
                  <span>•</span>
                  {getStatusBadge(vendor.status)}
                </DialogDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => onEditVendor(vendor)}>
                  Edit
                </Button>
                {!vendor.archived_at && (
                  <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10" onClick={() => onArchiveVendor(vendor)}>
                    Archive
                  </Button>
                )}
              </div>
            </div>
          </DialogHeader>

          {/* Quick Contact & Summary Bar */}
          <div className="grid grid-cols-2 gap-3 rounded-lg border bg-card p-3 sm:grid-cols-4 text-sm">
            <div>
              <span className="text-xs text-muted-foreground">Contact Person</span>
              <p className="font-medium flex items-center gap-1.5 mt-0.5">
                <User className="h-3.5 w-3.5 text-muted-foreground" />
                {vendor.contact_name || "Not recorded"}
              </p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Phone</span>
              <p className="font-medium flex items-center gap-1.5 mt-0.5">
                <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                {vendor.phone || "—"}
              </p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Quotations</span>
              <p className="font-medium flex items-center gap-1.5 mt-0.5">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                {details?.quotes.length ?? vendor.quotes_count} recorded
              </p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Total Paid / Spent</span>
              <p className="font-medium flex items-center gap-1.5 mt-0.5 text-emerald-700">
                <Receipt className="h-3.5 w-3.5 text-emerald-600" />
                ₹{parseFloat(vendor.total_spent_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-border">
            <button
              type="button"
              onClick={() => setActiveTab("quotes")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "quotes"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              Quotations ({details?.quotes.length ?? vendor.quotes_count})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("expenses")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "expenses"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              Expenses & Budget ({details?.associated_expenses.length ?? vendor.associated_expenses_count})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "overview"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              Overview & Notes
            </button>
          </div>

          {/* Tab Content */}
          <div className="py-2">
            {loading ? (
              <div className="py-8 text-center text-sm text-muted-foreground">Loading details...</div>
            ) : activeTab === "quotes" ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold">Recorded Commercial Quotations</h4>
                  <Button
                    size="sm"
                    className="gap-1.5"
                    onClick={() => {
                      setEditingQuote(null);
                      setQuoteDialogOpen(true);
                    }}
                  >
                    <Plus className="h-4 w-4" /> Add Quotation
                  </Button>
                </div>

                {!details?.quotes.length ? (
                  <div className="rounded-lg border border-dashed p-8 text-center">
                    <FileText className="mx-auto h-8 w-8 text-muted-foreground" />
                    <p className="mt-2 text-sm font-medium">No quotations recorded yet</p>
                    <p className="text-xs text-muted-foreground">
                      Record quotes received to compare pricing, guest capacities and deliverables side-by-side.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {details.quotes.map((q) => (
                      <div key={q.id} className="rounded-lg border bg-card p-4 transition-all">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <span className="text-xl font-bold font-serif text-primary">
                              ₹{parseFloat(q.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </span>
                            <span className="ml-2 text-xs text-muted-foreground">{q.currency}</span>
                            <div className="mt-1">{getQuoteBadge(q.status)}</div>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditingQuote(q);
                                setQuoteDialogOpen(true);
                              }}
                            >
                              Edit
                            </Button>
                            {q.status !== "accepted" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                                onClick={() => handleUpdateQuoteStatus(q, "accepted")}
                              >
                                Accept Quote
                              </Button>
                            )}
                            {q.status !== "shortlisted" && q.status !== "accepted" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-purple-700 border-purple-300 hover:bg-purple-50"
                                onClick={() => handleUpdateQuoteStatus(q, "shortlisted")}
                              >
                                Shortlist
                              </Button>
                            )}
                          </div>
                        </div>

                        <p className="mt-3 text-sm font-medium text-foreground">{q.scope_summary}</p>

                        <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                          {q.valid_until && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5" />
                              Valid until {formatDate(q.valid_until)}
                            </span>
                          )}
                          <span>Recorded on {formatDate(q.created_at)}</span>
                        </div>

                        {q.notes && (
                          <div className="mt-2.5 rounded bg-muted/50 p-2 text-xs text-muted-foreground">
                            <strong>Note:</strong> {q.notes}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : activeTab === "expenses" ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold">BudgetAI Associated Expenses</h4>
                    <p className="text-xs text-muted-foreground">
                      Financial ledger records associated with {vendor.name}.
                    </p>
                  </div>
                  <Link href={routes.eventBudget(eventId)}>
                    <Button variant="outline" size="sm" className="gap-1.5">
                      <ExternalLink className="h-3.5 w-3.5" /> Open BudgetAI
                    </Button>
                  </Link>
                </div>

                {!details?.associated_expenses.length ? (
                  <div className="rounded-lg border border-dashed p-8 text-center">
                    <Receipt className="mx-auto h-8 w-8 text-muted-foreground" />
                    <p className="mt-2 text-sm font-medium">No expenses linked to this vendor yet</p>
                    <p className="text-xs text-muted-foreground">
                      Record deposits or payments in BudgetAI with this vendor selected to track spending.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {details.associated_expenses.map((e) => (
                      <div key={e.id} className="flex items-center justify-between rounded-lg border bg-card p-3 text-sm">
                        <div>
                          <p className="font-medium text-foreground">{e.description}</p>
                          <p className="text-xs text-muted-foreground">{e.expense_date}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-primary">
                            ₹{parseFloat(e.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </p>
                          <Badge variant="outline" className="capitalize text-xs">
                            {e.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-4 text-sm">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border p-3">
                    <span className="text-xs text-muted-foreground">Official Email</span>
                    <p className="mt-1 font-medium flex items-center gap-1.5">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      {vendor.email || "Not specified"}
                    </p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <span className="text-xs text-muted-foreground">Portfolio / Website</span>
                    <p className="mt-1 font-medium flex items-center gap-1.5">
                      <ExternalLink className="h-4 w-4 text-muted-foreground" />
                      {vendor.website_url ? (
                        <a
                          href={vendor.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          {vendor.website_url}
                        </a>
                      ) : (
                        "Not specified"
                      )}
                    </p>
                  </div>
                </div>

                <div className="rounded-lg border p-3">
                  <span className="text-xs text-muted-foreground">Private Host Notes</span>
                  <p className="mt-1 whitespace-pre-wrap text-foreground">
                    {vendor.notes || "No private notes recorded."}
                  </p>
                </div>

                <div className="rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground space-y-1">
                  <p>Created: {formatDate(vendor.created_at)}</p>
                  <p>Last modified: {formatDate(vendor.updated_at)}</p>
                  {vendor.archived_at && <p className="text-destructive font-medium">Archived on: {formatDate(vendor.archived_at)}</p>}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Quote Dialog */}
      <QuoteFormDialog
        open={quoteDialogOpen}
        onOpenChange={setQuoteDialogOpen}
        vendorName={vendor.name}
        quote={editingQuote}
        onSubmit={handleSaveQuote}
      />
    </>
  );
}
