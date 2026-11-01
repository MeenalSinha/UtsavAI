export type GiftItemType = "physical" | "experience" | "cash_fund";
export type GiftMode = "individual" | "group";
export type GiftItemPriority = "high" | "medium" | "low";
export type GiftReservationStatus = "reserved" | "fulfilled" | "cancelled" | "expired";
export type GiftContributionStatus = "pledged" | "verified" | "cancelled";
export type VerificationMethod = "offline_cash" | "upi_direct" | "bank_transfer" | "gift_card" | "other";

export interface GiftRegistryDto {
  id: string;
  event_id: string;
  title: string;
  welcome_message: string | null;
  delivery_address: string | null;
  allow_group_gifting: boolean;
  is_public: boolean;
  status: "active" | "archived";
  share_link_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GiftRegistryCreatePayload {
  title?: string;
  welcome_message?: string | null;
  delivery_address?: string | null;
  allow_group_gifting?: boolean;
}

export interface GiftRegistryUpdatePayload {
  title?: string;
  welcome_message?: string | null;
  delivery_address?: string | null;
  allow_group_gifting?: boolean;
  status?: "active" | "archived";
}

export interface GiftRegistryShareLinkResponse {
  registry_id: string;
  share_token: string;
  share_url: string;
  expires_at: string | null;
}

export interface GiftRegistryShareLinkStatus {
  has_active_link: boolean;
  share_url: string | null;
  expires_at: string | null;
}

export interface GiftItemDto {
  id: string;
  registry_id: string;
  name: string;
  description: string | null;
  item_type: GiftItemType;
  gift_mode: GiftMode;
  target_amount: string | null;
  currency: string;
  external_url: string | null;
  image_url: string | null;
  priority: GiftItemPriority;
  sort_order: number;
  is_active: boolean;
  reservation_status: GiftReservationStatus | null;
  reserved_by_alias: string | null;
  pledged_amount: string;
  verified_amount: string;
  total_contributed: string;
  remaining_amount: string | null;
  created_at: string;
  updated_at: string;
}

export interface GiftItemCreatePayload {
  name: string;
  description?: string | null;
  item_type?: GiftItemType;
  gift_mode?: GiftMode;
  target_amount?: string | number | null;
  currency?: string;
  external_url?: string | null;
  image_url?: string | null;
  priority?: GiftItemPriority;
  sort_order?: number;
}

export interface GiftItemUpdatePayload {
  name?: string;
  description?: string | null;
  item_type?: GiftItemType;
  gift_mode?: GiftMode;
  target_amount?: string | number | null;
  currency?: string;
  external_url?: string | null;
  image_url?: string | null;
  priority?: GiftItemPriority;
  sort_order?: number;
  is_active?: boolean;
}

export interface GiftReservationDto {
  id: string;
  gift_item_id: string;
  guest_alias: string | null;
  notes: string | null;
  status: GiftReservationStatus;
  expires_at: string | null;
  created_at: string;
}

export interface GiftContributionDto {
  id: string;
  gift_item_id: string;
  guest_alias: string | null;
  amount: string;
  currency: string;
  status: GiftContributionStatus;
  verification_method: VerificationMethod | null;
  verification_notes: string | null;
  verified_at: string | null;
  created_at: string;
}

export interface HostVerifyContributionPayload {
  verification_method: VerificationMethod;
  verification_notes?: string | null;
}

export interface GiftRegistryOverviewDto {
  registry: GiftRegistryDto;
  share_link: GiftRegistryShareLinkStatus;
  total_items: number;
  active_items: number;
  reserved_items: number;
  group_items: number;
  total_pledged: string;
  total_verified: string;
  currency: string;
}

// ---------------- Public Guest Interfaces ----------------

export interface PublicGiftItemDto {
  id: string;
  name: string;
  description: string | null;
  item_type: GiftItemType;
  gift_mode: GiftMode;
  target_amount: string | null;
  currency: string;
  external_url: string | null;
  image_url: string | null;
  priority: GiftItemPriority;
  sort_order: number;
  is_available: boolean;
  reservation_status: GiftReservationStatus | null;
  total_contributed: string;
  remaining_amount: string | null;
}

export interface PublicGiftRegistryDto {
  registry_id: string;
  event_title: string;
  registry_title: string;
  welcome_message: string | null;
  delivery_address: string | null;
  allow_group_gifting: boolean;
  items: PublicGiftItemDto[];
}

export interface PublicReservePayload {
  idempotency_key: string;
  guest_alias?: string | null;
  notes?: string | null;
}

export interface PublicReservationConfirmationDto {
  reservation_id: string;
  gift_item_id: string;
  cancellation_token: string;
  message: string;
}

export interface PublicCancelReservationPayload {
  cancellation_token: string;
}

export interface PublicContributionPayload {
  idempotency_key: string;
  guest_alias?: string | null;
  amount: number | string;
  currency?: string;
}

export interface PublicContributionConfirmationDto {
  contribution_id: string;
  gift_item_id: string;
  amount: string;
  currency: string;
  message: string;
}
