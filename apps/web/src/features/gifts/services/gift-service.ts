import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type {
  GiftContributionDto,
  GiftItemCreatePayload,
  GiftItemDto,
  GiftItemUpdatePayload,
  GiftRegistryCreatePayload,
  GiftRegistryDto,
  GiftRegistryOverviewDto,
  GiftRegistryShareLinkResponse,
  GiftRegistryShareLinkStatus,
  GiftRegistryUpdatePayload,
  GiftReservationDto,
  HostVerifyContributionPayload,
  PublicCancelReservationPayload,
  PublicContributionConfirmationDto,
  PublicContributionPayload,
  PublicGiftRegistryDto,
  PublicReservationConfirmationDto,
  PublicReservePayload,
} from "../types";

const PUBLIC_PREFIX = "/api/public";

async function publicFetch<T>(
  path: string,
  init: Omit<RequestInit, "body"> & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const finalHeaders = new Headers(headers);
  finalHeaders.set("Accept", "application/json");
  if (json !== undefined) finalHeaders.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(`${PUBLIC_PREFIX}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: json === undefined ? undefined : JSON.stringify(json),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Could not reach the server. Please check your connection.");
  }

  if (!res.ok) {
    let payload: unknown;
    try {
      payload = await res.json();
    } catch {
      payload = null;
    }
    const err = (payload as { error?: { code?: string; message?: string; details?: Record<string, unknown> } })
      ?.error;
    throw new ApiError(
      res.status,
      err?.code ?? "UNKNOWN_ERROR",
      err?.message ?? "An error occurred while processing your request.",
      err?.details,
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const giftService = {
  // ---------------- Host Operations ----------------
  async getOverview(eventId: string): Promise<GiftRegistryOverviewDto> {
    return (await apiFetch<GiftRegistryOverviewDto>(`/events/${eventId}/gift-registry/overview`)).data;
  },

  async getRegistry(eventId: string): Promise<GiftRegistryDto | null> {
    try {
      return (await apiFetch<GiftRegistryDto>(`/events/${eventId}/gift-registry`)).data;
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return null;
      throw err;
    }
  },

  async createRegistry(eventId: string, payload: GiftRegistryCreatePayload): Promise<GiftRegistryDto> {
    return (
      await apiFetch<GiftRegistryDto>(`/events/${eventId}/gift-registry`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async updateRegistry(eventId: string, payload: GiftRegistryUpdatePayload): Promise<GiftRegistryDto> {
    return (
      await apiFetch<GiftRegistryDto>(`/events/${eventId}/gift-registry`, {
        method: "PATCH",
        json: payload,
      })
    ).data;
  },

  async getShareLink(eventId: string): Promise<GiftRegistryShareLinkStatus> {
    return (await apiFetch<GiftRegistryShareLinkStatus>(`/events/${eventId}/gift-registry/share-link`)).data;
  },

  async rotateShareLink(eventId: string): Promise<GiftRegistryShareLinkResponse> {
    return (
      await apiFetch<GiftRegistryShareLinkResponse>(`/events/${eventId}/gift-registry/share-link`, {
        method: "POST",
      })
    ).data;
  },

  async revokeShareLink(eventId: string): Promise<void> {
    await apiFetch<void>(`/events/${eventId}/gift-registry/share-link`, {
      method: "DELETE",
    });
  },

  async listItems(eventId: string): Promise<GiftItemDto[]> {
    return (await apiFetch<GiftItemDto[]>(`/events/${eventId}/gift-registry/items`)).data;
  },

  async createItem(eventId: string, payload: GiftItemCreatePayload): Promise<GiftItemDto> {
    return (
      await apiFetch<GiftItemDto>(`/events/${eventId}/gift-registry/items`, {
        method: "POST",
        json: payload,
      })
    ).data;
  },

  async updateItem(eventId: string, itemId: string, payload: GiftItemUpdatePayload): Promise<GiftItemDto> {
    return (
      await apiFetch<GiftItemDto>(`/events/${eventId}/gift-registry/items/${itemId}`, {
        method: "PATCH",
        json: payload,
      })
    ).data;
  },

  async deleteItem(eventId: string, itemId: string): Promise<void> {
    await apiFetch<void>(`/events/${eventId}/gift-registry/items/${itemId}`, {
      method: "DELETE",
    });
  },

  async listReservations(eventId: string): Promise<GiftReservationDto[]> {
    return (await apiFetch<GiftReservationDto[]>(`/events/${eventId}/gift-registry/reservations`)).data;
  },

  async cancelReservation(eventId: string, reservationId: string): Promise<void> {
    await apiFetch<void>(`/events/${eventId}/gift-registry/reservations/${reservationId}/cancel`, {
      method: "POST",
    });
  },

  async listContributions(eventId: string): Promise<GiftContributionDto[]> {
    return (await apiFetch<GiftContributionDto[]>(`/events/${eventId}/gift-registry/contributions`)).data;
  },

  async verifyContribution(
    eventId: string,
    contributionId: string,
    payload: HostVerifyContributionPayload,
  ): Promise<GiftContributionDto> {
    return (
      await apiFetch<GiftContributionDto>(
        `/events/${eventId}/gift-registry/contributions/${contributionId}/verify`,
        {
          method: "POST",
          json: payload,
        },
      )
    ).data;
  },

  // ---------------- Public Guest Operations ----------------
  async getPublicRegistry(shareToken: string): Promise<PublicGiftRegistryDto> {
    return await publicFetch<PublicGiftRegistryDto>(`/registries/${shareToken}`);
  },

  async reservePublicItem(
    shareToken: string,
    itemId: string,
    payload: PublicReservePayload,
  ): Promise<PublicReservationConfirmationDto> {
    return await publicFetch<PublicReservationConfirmationDto>(
      `/registries/${shareToken}/items/${itemId}/reserve`,
      {
        method: "POST",
        json: payload,
      },
    );
  },

  async cancelPublicReservation(
    shareToken: string,
    reservationId: string,
    payload: PublicCancelReservationPayload,
  ): Promise<void> {
    await publicFetch<void>(
      `/registries/${shareToken}/reservations/${reservationId}/cancel`,
      {
        method: "POST",
        json: payload,
      },
    );
  },

  async contributePublicItem(
    shareToken: string,
    itemId: string,
    payload: PublicContributionPayload,
  ): Promise<PublicContributionConfirmationDto> {
    return await publicFetch<PublicContributionConfirmationDto>(
      `/registries/${shareToken}/items/${itemId}/contribute`,
      {
        method: "POST",
        json: payload,
      },
    );
  },
};
