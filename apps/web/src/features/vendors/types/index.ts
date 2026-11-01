import type { ExpenseDto } from "@/types/api";

export type VendorStatus = "identified" | "contacted" | "quoted" | "shortlisted" | "booked" | "declined";
export type QuoteStatus = "received" | "shortlisted" | "accepted" | "rejected" | "expired";

export interface VendorDto {
  id: string;
  event_id: string;
  category: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website_url?: string | null;
  notes?: string | null;
  status: VendorStatus;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;

  quotes_count: number;
  latest_quote_amount?: string | null;
  latest_quote_currency?: string | null;
  associated_expenses_count: number;
  total_spent_amount: string;
}

export interface VendorQuoteDto {
  id: string;
  vendor_id: string;
  amount: string;
  currency: string;
  scope_summary: string;
  valid_until?: string | null;
  notes?: string | null;
  status: QuoteStatus;
  created_at: string;
  updated_at: string;
}

export interface VendorDetailDto extends VendorDto {
  quotes: VendorQuoteDto[];
  associated_expenses: ExpenseDto[];
}

export interface QuotationComparisonItemDto {
  vendor_id: string;
  vendor_name: string;
  vendor_status: VendorStatus;
  quote_id: string;
  amount: string;
  currency: string;
  scope_summary: string;
  valid_until?: string | null;
  status: QuoteStatus;
  missing_fields: string[];
  comparison_warnings: string[];
  updated_at: string;
}

export interface QuotationComparisonGroupDto {
  category: string;
  quotes: QuotationComparisonItemDto[];
  category_warnings: string[];
  price_range_min?: string | null;
  price_range_max?: string | null;
}

export interface QuotationComparisonDto {
  event_id: string;
  currency: string;
  groups: QuotationComparisonGroupDto[];
  total_quotes_compared: number;
}

export interface VendorCategorySummaryDto {
  category: string;
  vendor_count: number;
  quoted_count: number;
  shortlisted_count: number;
  booked_count: number;
}

export interface VendorSummaryDto {
  total_vendors: number;
  identified_count: number;
  contacted_count: number;
  quoted_count: number;
  shortlisted_count: number;
  booked_count: number;
  declined_count: number;
  categories: VendorCategorySummaryDto[];
  quote_count: number;
  pending_decisions: number;
}

export interface VendorCreatePayload {
  category: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website_url?: string | null;
  notes?: string | null;
}

export interface VendorUpdatePayload {
  category?: string;
  name?: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  website_url?: string | null;
  notes?: string | null;
  status?: VendorStatus;
}

export interface VendorQuoteCreatePayload {
  amount: string;
  currency?: string;
  scope_summary: string;
  valid_until?: string | null;
  notes?: string | null;
}

export interface VendorQuoteUpdatePayload {
  amount?: string;
  currency?: string;
  scope_summary?: string;
  valid_until?: string | null;
  notes?: string | null;
  status?: QuoteStatus;
}
