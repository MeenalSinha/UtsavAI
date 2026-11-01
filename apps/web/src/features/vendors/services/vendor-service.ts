import { apiFetch } from "@/lib/api/client";
import type {
  QuotationComparisonDto,
  VendorCreatePayload,
  VendorDetailDto,
  VendorDto,
  VendorQuoteCreatePayload,
  VendorQuoteDto,
  VendorQuoteUpdatePayload,
  VendorSummaryDto,
  VendorUpdatePayload,
} from "../types";

export const vendorService = {
  async listVendors(
    eventId: string,
    params?: { category?: string; status?: string; search?: string; include_archived?: boolean },
  ): Promise<VendorDto[]> {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.status) q.set("status", params.status);
    if (params?.search) q.set("search", params.search);
    if (params?.include_archived) q.set("include_archived", "true");
    const queryStr = q.toString() ? `?${q.toString()}` : "";
    return (await apiFetch<VendorDto[]>(`/events/${eventId}/vendors${queryStr}`)).data;
  },

  async getVendorSummary(eventId: string): Promise<VendorSummaryDto> {
    return (await apiFetch<VendorSummaryDto>(`/events/${eventId}/vendors/summary`)).data;
  },

  async getVendor(eventId: string, vendorId: string): Promise<VendorDetailDto> {
    return (await apiFetch<VendorDetailDto>(`/events/${eventId}/vendors/${vendorId}`)).data;
  },

  async createVendor(eventId: string, payload: VendorCreatePayload): Promise<VendorDto> {
    return (
      await apiFetch<VendorDto>(`/events/${eventId}/vendors`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async updateVendor(eventId: string, vendorId: string, payload: VendorUpdatePayload): Promise<VendorDto> {
    return (
      await apiFetch<VendorDto>(`/events/${eventId}/vendors/${vendorId}`, {
        method: "PATCH",
        json: payload,
      })
    ).data;
  },

  async archiveVendor(eventId: string, vendorId: string): Promise<void> {
    await apiFetch<void>(`/events/${eventId}/vendors/${vendorId}`, {
      method: "DELETE",
    });
  },

  async listQuotes(eventId: string, vendorId: string): Promise<VendorQuoteDto[]> {
    return (await apiFetch<VendorQuoteDto[]>(`/events/${eventId}/vendors/${vendorId}/quotes`)).data;
  },

  async createQuote(eventId: string, vendorId: string, payload: VendorQuoteCreatePayload): Promise<VendorQuoteDto> {
    return (
      await apiFetch<VendorQuoteDto>(`/events/${eventId}/vendors/${vendorId}/quotes`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async updateQuote(
    eventId: string,
    vendorId: string,
    quoteId: string,
    payload: VendorQuoteUpdatePayload,
  ): Promise<VendorQuoteDto> {
    return (
      await apiFetch<VendorQuoteDto>(`/events/${eventId}/vendors/${vendorId}/quotes/${quoteId}`, {
        method: "PATCH",
        json: payload,
      })
    ).data;
  },

  async getQuotationComparison(eventId: string): Promise<QuotationComparisonDto> {
    return (await apiFetch<QuotationComparisonDto>(`/events/${eventId}/vendor-quote-comparison`)).data;
  },
};
