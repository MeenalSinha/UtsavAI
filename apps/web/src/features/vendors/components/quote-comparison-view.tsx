"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, FileText, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { vendorService } from "../services/vendor-service";
import type { QuotationComparisonDto, QuotationComparisonItemDto } from "../types";

interface QuoteComparisonViewProps {
  eventId: string;
  onRefreshRequested?: () => void;
}

export function QuoteComparisonView({ eventId, onRefreshRequested }: QuoteComparisonViewProps) {
  const [data, setData] = useState<QuotationComparisonDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = useCallback(() => {
    setLoading(true);
    vendorService
      .getQuotationComparison(eventId)
      .then(setData)
      .catch((err) => console.error("Failed to load comparison", err))
      .finally(() => setLoading(false));
  }, [eventId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStatusChange = async (item: QuotationComparisonItemDto, newStatus: "shortlisted" | "accepted") => {
    setActionLoading(item.quote_id);
    try {
      await vendorService.updateQuote(eventId, item.vendor_id, item.quote_id, { status: newStatus });
      loadData();
      onRefreshRequested?.();
    } catch (err) {
      console.error("Failed to update quote status", err);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border bg-card p-12 text-center text-sm text-muted-foreground">
        Evaluating and grouping commercial quotations...
      </div>
    );
  }

  if (!data || data.total_quotes_compared === 0) {
    return (
      <div className="rounded-xl border border-dashed bg-card p-12 text-center">
        <FileText className="mx-auto h-12 w-12 text-muted-foreground/60" />
        <h3 className="mt-4 font-serif text-lg font-medium text-foreground">No Quotations to Compare Yet</h3>
        <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
          Record at least two quotations from your vendors to evaluate pricing, deliverables, guest capacities, and validity periods side by side.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Informative Guidance Banner */}
      <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm text-primary">
        <Info className="h-5 w-5 shrink-0 text-primary mt-0.5" />
        <div>
          <p className="font-semibold">Deterministic Scope & Price Comparison</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Quotations are grouped by category and evaluated strictly on documented deliverables, guest counts, and validity windows. Lowest quoted amount does not imply superior value or quality.
          </p>
        </div>
      </div>

      {data.groups.map((group) => (
        <div key={group.category} className="space-y-4 rounded-xl border bg-card p-6 shadow-sm">
          {/* Group Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-serif text-xl font-bold capitalize text-primary">{group.category}</h3>
                <Badge variant="secondary" className="rounded-full">
                  {group.quotes.length} {group.quotes.length === 1 ? "quote" : "quotes"}
                </Badge>
              </div>
              {group.price_range_min && group.price_range_max && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Price Range: ₹{parseFloat(group.price_range_min).toLocaleString("en-IN")} – ₹{parseFloat(group.price_range_max).toLocaleString("en-IN")} {data.currency}
                </p>
              )}
            </div>
          </div>

          {/* Category Warnings / Scope Discrepancy Alerts */}
          {group.category_warnings.length > 0 && (
            <div className="space-y-2">
              {group.category_warnings.map((warn, idx) => (
                <div key={idx} className="flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                  <span>{warn}</span>
                </div>
              ))}
            </div>
          )}

          {/* Quotations Grid */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {group.quotes.map((q) => {
              const isAccepted = q.status === "accepted";
              const isShortlisted = q.status === "shortlisted";

              return (
                <div
                  key={q.quote_id}
                  className={`flex flex-col justify-between rounded-lg border p-4 transition-all ${
                    isAccepted
                      ? "border-emerald-500 bg-emerald-50/30 ring-1 ring-emerald-500"
                      : isShortlisted
                      ? "border-purple-400 bg-purple-50/20"
                      : "bg-background hover:border-primary/40"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-serif font-bold text-foreground text-base">{q.vendor_name}</h4>
                        <span className="text-xs text-muted-foreground capitalize">
                          Vendor: {q.vendor_status}
                        </span>
                      </div>
                      <Badge
                        variant={
                          isAccepted
                            ? "default"
                            : isShortlisted
                            ? "secondary"
                            : "outline"
                        }
                        className={
                          isAccepted
                            ? "bg-emerald-600 text-white"
                            : isShortlisted
                            ? "bg-purple-100 text-purple-800"
                            : ""
                        }
                      >
                        {q.status}
                      </Badge>
                    </div>

                    <div className="rounded-lg bg-card border p-3">
                      <span className="text-2xl font-bold font-serif text-primary">
                        ₹{parseFloat(q.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                      <span className="ml-1.5 text-xs text-muted-foreground">{q.currency}</span>
                    </div>

                    {/* Scope Summary */}
                    <div>
                      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Scope Deliverables</span>
                      <p className="mt-1 text-sm text-foreground leading-relaxed">
                        {q.scope_summary}
                      </p>
                    </div>

                    {/* Validity Info */}
                    <div className="text-xs text-muted-foreground">
                      {q.valid_until ? (
                        <span>Valid until: <strong>{q.valid_until}</strong></span>
                      ) : (
                        <span className="text-amber-700 italic">No validity date specified</span>
                      )}
                    </div>

                    {/* Missing Fields Indicators */}
                    {q.missing_fields.length > 0 && (
                      <div className="rounded border border-amber-200 bg-amber-50/50 p-2 space-y-1">
                        <span className="text-[11px] font-semibold text-amber-800 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> Incomplete Information:
                        </span>
                        <ul className="list-disc pl-4 text-[11px] text-amber-700">
                          {q.missing_fields.map((mf, i) => (
                            <li key={i}>{mf}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Quotation Warnings */}
                    {q.comparison_warnings.length > 0 && (
                      <div className="rounded border border-destructive/20 bg-destructive/10 p-2 space-y-1">
                        <span className="text-[11px] font-semibold text-destructive flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> Note:
                        </span>
                        <ul className="list-disc pl-4 text-[11px] text-destructive">
                          {q.comparison_warnings.map((cw, i) => (
                            <li key={i}>{cw}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Action Bar */}
                  <div className="mt-4 pt-3 border-t flex items-center justify-end gap-2">
                    {!isAccepted && (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={actionLoading === q.quote_id}
                        className="text-emerald-700 border-emerald-300 hover:bg-emerald-50 text-xs"
                        onClick={() => handleStatusChange(q, "accepted")}
                      >
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Book Proposal
                      </Button>
                    )}
                    {!isShortlisted && !isAccepted && (
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={actionLoading === q.quote_id}
                        className="text-purple-700 hover:bg-purple-50 text-xs"
                        onClick={() => handleStatusChange(q, "shortlisted")}
                      >
                        Shortlist
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
