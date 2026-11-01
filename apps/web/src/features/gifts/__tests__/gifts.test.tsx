import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GiftWorkspace } from "../components/gift-workspace";
import { PublicRegistryView } from "../components/public-registry-view";
import { giftService } from "../services/gift-service";
import type {
  GiftContributionDto,
  GiftItemDto,
  GiftRegistryDto,
  GiftRegistryOverviewDto,
  GiftReservationDto,
  PublicGiftRegistryDto,
} from "../types";

vi.mock("../services/gift-service");

const mockRegistry: GiftRegistryDto = {
  id: "reg-1",
  event_id: "event-1",
  title: "Aarav & Meera Wedding Wishlist",
  welcome_message: "Thank you for celebrating with us!",
  delivery_address: "123 Heritage Lane, Jaipur",
  allow_group_gifting: true,
  is_public: true,
  status: "active",
  share_link_active: true,
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
};

const mockOverview: GiftRegistryOverviewDto = {
  registry: mockRegistry,
  share_link: {
    has_active_link: true,
    share_url: "http://localhost:3000/g/sampletoken123",
    expires_at: null,
  },
  total_items: 2,
  active_items: 2,
  reserved_items: 1,
  group_items: 1,
  total_pledged: "25000.00",
  total_verified: "10000.00",
  currency: "INR",
};

const mockItems: GiftItemDto[] = [
  {
    id: "item-1",
    registry_id: "reg-1",
    name: "Espresso Coffee Machine",
    description: "Compact dual-boiler machine",
    item_type: "physical",
    gift_mode: "individual",
    target_amount: "45000.00",
    currency: "INR",
    external_url: "https://example.com/coffee",
    image_url: null,
    priority: "high",
    sort_order: 1,
    is_active: true,
    reservation_status: "reserved",
    reserved_by_alias: "Sunil Uncle",
    pledged_amount: "0.00",
    verified_amount: "0.00",
    total_contributed: "0.00",
    remaining_amount: null,
    created_at: "2026-11-01T00:00:00Z",
    updated_at: "2026-11-01T00:00:00Z",
  },
  {
    id: "item-2",
    registry_id: "reg-1",
    name: "Udaipur Honeymoon Stay",
    description: "Lake Palace 3-night stay",
    item_type: "experience",
    gift_mode: "group",
    target_amount: "100000.00",
    currency: "INR",
    external_url: null,
    image_url: null,
    priority: "high",
    sort_order: 2,
    is_active: true,
    reservation_status: null,
    reserved_by_alias: null,
    pledged_amount: "25000.00",
    verified_amount: "10000.00",
    total_contributed: "35000.00",
    remaining_amount: "65000.00",
    created_at: "2026-11-01T00:00:00Z",
    updated_at: "2026-11-01T00:00:00Z",
  },
];

const mockReservations: GiftReservationDto[] = [
  {
    id: "res-1",
    gift_item_id: "item-1",
    guest_alias: "Sunil Uncle",
    notes: "Can't wait to celebrate!",
    status: "reserved",
    expires_at: null,
    created_at: "2026-11-01T00:00:00Z",
  },
];

const mockContributions: GiftContributionDto[] = [
  {
    id: "cont-1",
    gift_item_id: "item-2",
    guest_alias: "Priya & Friends",
    amount: "25000.00",
    currency: "INR",
    status: "pledged",
    verification_method: null,
    verification_notes: null,
    verified_at: null,
    created_at: "2026-11-01T00:00:00Z",
  },
];

describe("GiftWorkspace (Host)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(giftService.getRegistry).mockResolvedValue(mockRegistry);
    vi.mocked(giftService.getOverview).mockResolvedValue(mockOverview);
    vi.mocked(giftService.listItems).mockResolvedValue(mockItems);
    vi.mocked(giftService.listReservations).mockResolvedValue(mockReservations);
    vi.mocked(giftService.listContributions).mockResolvedValue(mockContributions);
  });

  it("renders host overview metrics and item wishlist", async () => {
    render(<GiftWorkspace eventId="event-1" />);

    expect(await screen.findByText("GiftCircle Registry")).toBeInTheDocument();
    expect(screen.getByText("Total Items")).toBeInTheDocument();
    expect(screen.getByText("Claimed / Reserved")).toBeInTheDocument();
    expect(screen.getByText("Guest Pledges")).toBeInTheDocument();
    expect(screen.getByText("Verified Received")).toBeInTheDocument();

    expect(screen.getByText("Espresso Coffee Machine")).toBeInTheDocument();
    expect(screen.getByText("Udaipur Honeymoon Stay")).toBeInTheDocument();
    expect(screen.getByText("Individual")).toBeInTheDocument();
    expect(screen.getByText("Group Gift")).toBeInTheDocument();
  });

  it("opens add gift item modal when clicking Add Gift Item", async () => {
    const user = userEvent.setup();
    render(<GiftWorkspace eventId="event-1" />);

    const addButton = await screen.findByRole("button", { name: /add gift item/i });
    await user.click(addButton);

    expect(await screen.findByText("Add Gift to Registry")).toBeInTheDocument();
    expect(screen.getByLabelText(/item name \*/i)).toBeInTheDocument();
  });

  it("renders reservations tab with active guest reservations", async () => {
    const user = userEvent.setup();
    render(<GiftWorkspace eventId="event-1" />);

    const tab = await screen.findByRole("tab", { name: /reservations/i });
    await user.click(tab);

    expect(await screen.findByText("Active Individual Reservations")).toBeInTheDocument();
    expect(screen.getByText("Sunil Uncle")).toBeInTheDocument();
    expect(screen.getByText("Can't wait to celebrate!")).toBeInTheDocument();
  });
});

describe("PublicRegistryView (Guest)", () => {
  const publicData: PublicGiftRegistryDto = {
    registry_id: "reg-1",
    event_title: "Aarav & Meera's Wedding",
    registry_title: "Our Wedding Wishlist",
    welcome_message: "Thank you for celebrating with us!",
    delivery_address: "123 Heritage Lane, Jaipur",
    allow_group_gifting: true,
    items: [
      {
        id: "item-1",
        name: "Espresso Coffee Machine",
        description: "Compact dual-boiler machine",
        item_type: "physical",
        gift_mode: "individual",
        target_amount: "45000.00",
        currency: "INR",
        external_url: null,
        image_url: null,
        priority: "high",
        sort_order: 1,
        is_available: true,
        reservation_status: null,
        total_contributed: "0.00",
        remaining_amount: null,
      },
      {
        id: "item-2",
        name: "Udaipur Honeymoon Stay",
        description: "Lake Palace 3-night stay",
        item_type: "experience",
        gift_mode: "group",
        target_amount: "100000.00",
        currency: "INR",
        external_url: null,
        image_url: null,
        priority: "high",
        sort_order: 2,
        is_available: true,
        reservation_status: null,
        total_contributed: "35000.00",
        remaining_amount: "65000.00",
      },
    ],
  };

  it("renders public guest wishlist, transparency banner, and buttons", () => {
    render(<PublicRegistryView shareToken="sampletoken123" initialRegistry={publicData} />);

    expect(screen.getByText("Aarav & Meera's Wedding")).toBeInTheDocument();
    expect(screen.getByText("Our Wedding Wishlist")).toBeInTheDocument();
    expect(screen.getByText("Direct-to-Couple Registry")).toBeInTheDocument();
    expect(screen.getByText(/no credit card or banking information is collected/i)).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /reserve this gift/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /contribute any amount/i })).toBeInTheDocument();
  });

  it("opens reservation dialog when clicking Reserve This Gift", async () => {
    const user = userEvent.setup();
    render(<PublicRegistryView shareToken="sampletoken123" initialRegistry={publicData} />);

    await user.click(screen.getByRole("button", { name: /reserve this gift/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/no online payment required/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/your name or family alias/i)).toBeInTheDocument();
  });

  it("opens group contribute dialog when clicking Contribute Any Amount", async () => {
    const user = userEvent.setup();
    render(<PublicRegistryView shareToken="sampletoken123" initialRegistry={publicData} />);

    await user.click(screen.getByRole("button", { name: /contribute any amount/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/target goal/i)).toBeInTheDocument();
    expect(screen.getByText(/offline settlement/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/pledge amount/i)).toBeInTheDocument();
  });
});
