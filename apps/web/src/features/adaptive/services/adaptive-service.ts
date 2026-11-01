import { apiFetch } from "@/lib/api/client";
import type {
  ChangeProposal,
  ChangeProposalCreate,
  InterpretedChangeResponse,
  ProposalAcceptRequest,
  ProposalRejectRequest,
} from "../types";

export const adaptiveService = {
  async listProposals(eventId: string, status?: string): Promise<ChangeProposal[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return (await apiFetch<ChangeProposal[]>(`/events/${eventId}/change-proposals${query}`)).data;
  },

  async getProposal(eventId: string, proposalId: string): Promise<ChangeProposal> {
    return (await apiFetch<ChangeProposal>(`/events/${eventId}/change-proposals/${proposalId}`)).data;
  },

  async createProposal(eventId: string, payload: ChangeProposalCreate): Promise<ChangeProposal> {
    return (
      await apiFetch<ChangeProposal>(`/events/${eventId}/change-proposals`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async interpretPrompt(eventId: string, prompt: string): Promise<InterpretedChangeResponse> {
    return (
      await apiFetch<InterpretedChangeResponse>(`/events/${eventId}/change-proposals/interpret`, {
        method: "POST",
        json: { prompt },
      })
    ).data;
  },

  async acceptProposal(
    eventId: string,
    proposalId: string,
    payload: ProposalAcceptRequest,
  ): Promise<ChangeProposal> {
    return (
      await apiFetch<ChangeProposal>(`/events/${eventId}/change-proposals/${proposalId}/accept`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async rejectProposal(
    eventId: string,
    proposalId: string,
    payload: ProposalRejectRequest,
  ): Promise<ChangeProposal> {
    return (
      await apiFetch<ChangeProposal>(`/events/${eventId}/change-proposals/${proposalId}/reject`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },
};
