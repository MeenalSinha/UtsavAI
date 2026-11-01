import http from "node:http";
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const playwrightPkg = path.join(root, "apps", "web", "node_modules", "playwright", "index.mjs");
const { chromium } = await import(pathToFileURL(playwrightPkg).href);

const EVENT_ID = "e0000000-0000-0000-0000-000000000001";
const USER_ID = "d0000000-0000-0000-0000-000000000001";
const USER_EMAIL = "demo.host@utsavai.test";
const SHARE_TOKEN = "demo-jaipur-aarav-meera";

// Output recordings directory
const recordingsDir = path.join(root, "recordings");
if (!fs.existsSync(recordingsDir)) fs.mkdirSync(recordingsDir, { recursive: true });

// ----------------- COMPLETE DATA STORE -----------------
const DEMO_USER = {
  id: USER_ID,
  user_id: USER_ID,
  aud: "authenticated",
  role: "authenticated",
  email: USER_EMAIL,
  email_confirmed_at: "2026-11-01T10:00:00Z",
  display_name: "Aarav Sharma",
  preferred_locale: "en-IN",
  timezone: "Asia/Kolkata",
  user_metadata: { displayName: "Aarav Sharma" },
};

const DEMO_PROFILE = {
  user_id: USER_ID,
  display_name: "Aarav Sharma",
  preferred_locale: "en-IN",
  timezone: "Asia/Kolkata",
  email: USER_EMAIL,
};

const DEMO_META = {
  event_types: [
    { key: "wedding", label: "Wedding", enabled: true },
    { key: "reception", label: "Reception", enabled: true },
    { key: "anniversary", label: "Anniversary", enabled: true },
  ],
  default_event_type: "wedding",
  currencies: ["INR", "USD", "EUR", "GBP"],
  default_currency: "INR",
  event_statuses: ["draft", "planning", "completed", "archived"],
  patchable_statuses: ["draft", "planning", "completed"],
  status_transitions: {
    draft: ["planning", "archived"],
    planning: ["completed", "archived"],
    completed: ["archived"],
  },
  locales: ["en-IN", "hi-IN", "en-US"],
  default_locale: "en-IN",
  default_timezone: "Asia/Kolkata",
  default_country_code: "IN",
  suggested_country_codes: ["IN", "AE", "US", "GB", "SG"],
  limits: { max_events_per_user: 20, max_functions_per_event: 30 },
};

const EVENT_DATA = {
  id: EVENT_ID,
  event_type: "wedding",
  title: "Aarav & Meera's Jaipur Royal Wedding",
  start_at: "2027-02-12T10:00:00Z",
  end_at: "2027-02-14T22:00:00Z",
  timezone: "Asia/Kolkata",
  location: {
    name: "Rambagh Palace",
    city: "Jaipur",
    region: "Rajasthan",
    country_code: "IN",
  },
  expected_guest_count: 300,
  currency: "INR",
  status: "planning",
  revision: 3,
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T14:30:00Z",
  archived_at: null,
  my_role: "owner",
};

const FUNCTIONS = [
  {
    id: "f0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    name: "Mehendi & Haldi Sunshine Ceremony",
    starts_at: "2027-02-12T14:00:00Z",
    ends_at: "2027-02-12T19:00:00Z",
    location_name: "Kesar Bagh Lawns, Rambagh Palace",
    notes: "Yellow and marigold floral themes. Live Rajasthani folk music.",
    sort_order: 1,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
  {
    id: "f0000000-0000-0000-0000-000000000002",
    event_id: EVENT_ID,
    name: "Sangeet Extravaganza & Musical Night",
    starts_at: "2027-02-12T19:30:00Z",
    ends_at: "2027-02-13T01:00:00Z",
    location_name: "Mubarak Mahal Grand Ballroom",
    notes: "Choreographed family dance performances followed by DJ set.",
    sort_order: 2,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
  {
    id: "f0000000-0000-0000-0000-000000000003",
    event_id: EVENT_ID,
    name: "Vedic Royal Wedding Pheras & Baraat",
    starts_at: "2027-02-13T17:00:00Z",
    ends_at: "2027-02-13T23:00:00Z",
    location_name: "Royal Courtyard Mandap",
    notes: "Grand royal elephant & vintage car Baraat arrival followed by twilight Pheras.",
    sort_order: 3,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
  {
    id: "f0000000-0000-0000-0000-000000000004",
    event_id: EVENT_ID,
    name: "Grand Gala Reception & Royal Banquet",
    starts_at: "2027-02-14T19:00:00Z",
    ends_at: "2027-02-14T23:59:00Z",
    location_name: "Maharani Gardens Palace Terrace",
    notes: "Black-tie reception with 7-course royal Rajasthani and Continental feast.",
    sort_order: 4,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
  },
];

const BUDGET = {
  id: "b0000000-0000-0000-0000-000000000001",
  event_id: EVENT_ID,
  total_limit: "2500000.00",
  currency: "INR",
  created_at: "2026-11-01T10:00:00Z",
  updated_at: "2026-11-01T10:00:00Z",
};

const BUDGET_CATEGORIES = [
  {
    id: "c0000000-0000-0000-0000-000000000001",
    budget_id: BUDGET.id,
    category_key: "venue",
    name: "Palace Venue & Hospitality",
    planned_amount: "1000000.00",
    sort_order: 1,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "400000.00",
    paid_amount: "400000.00",
    projected_amount: "1000000.00",
    remaining_amount: "600000.00",
    is_over_budget: false,
  },
  {
    id: "c0000000-0000-0000-0000-000000000002",
    budget_id: BUDGET.id,
    category_key: "catering",
    name: "Gourmet Royal Catering",
    planned_amount: "700000.00",
    sort_order: 2,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "150000.00",
    paid_amount: "150000.00",
    projected_amount: "700000.00",
    remaining_amount: "550000.00",
    is_over_budget: false,
  },
  {
    id: "c0000000-0000-0000-0000-000000000003",
    budget_id: BUDGET.id,
    category_key: "decor",
    name: "Heritage Floral & Mandap Decor",
    planned_amount: "300000.00",
    sort_order: 3,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "0.00",
    paid_amount: "0.00",
    projected_amount: "300000.00",
    remaining_amount: "300000.00",
    is_over_budget: false,
  },
  {
    id: "c0000000-0000-0000-0000-000000000004",
    budget_id: BUDGET.id,
    category_key: "photography",
    name: "Cinematography & Drone Photography",
    planned_amount: "250000.00",
    sort_order: 4,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "50000.00",
    paid_amount: "50000.00",
    projected_amount: "250000.00",
    remaining_amount: "200000.00",
    is_over_budget: false,
  },
  {
    id: "c0000000-0000-0000-0000-000000000005",
    budget_id: BUDGET.id,
    category_key: "entertainment",
    name: "Sangeet Artists & Sound / Lights",
    planned_amount: "150000.00",
    sort_order: 5,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "0.00",
    paid_amount: "0.00",
    projected_amount: "150000.00",
    remaining_amount: "150000.00",
    is_over_budget: false,
  },
  {
    id: "c0000000-0000-0000-0000-000000000006",
    budget_id: BUDGET.id,
    category_key: "contingency",
    name: "Contingency & Emergency Reserve",
    planned_amount: "100000.00",
    sort_order: 6,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    committed_amount: "0.00",
    paid_amount: "0.00",
    projected_amount: "100000.00",
    remaining_amount: "100000.00",
    is_over_budget: false,
  },
];

const EXPENSES = [
  {
    id: "x0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    budget_category_id: BUDGET_CATEGORIES[0].id,
    vendor_id: "v0000000-0000-0000-0000-000000000001",
    description: "Rambagh Palace 3-Day Venue Booking Advance Deposit",
    amount: "400000.00",
    currency: "INR",
    expense_date: "2026-11-01",
    status: "paid",
    created_by: USER_ID,
    created_at: "2026-11-01T11:00:00Z",
    updated_at: "2026-11-01T11:00:00Z",
  },
  {
    id: "x0000000-0000-0000-0000-000000000002",
    event_id: EVENT_ID,
    budget_category_id: BUDGET_CATEGORIES[1].id,
    vendor_id: "v0000000-0000-0000-0000-000000000002",
    description: "Rajputana Royal Caterers Menu Tasting & Chef Retainer",
    amount: "150000.00",
    currency: "INR",
    expense_date: "2026-11-01",
    status: "paid",
    created_by: USER_ID,
    created_at: "2026-11-01T12:00:00Z",
    updated_at: "2026-11-01T12:00:00Z",
  },
  {
    id: "x0000000-0000-0000-0000-000000000003",
    event_id: EVENT_ID,
    budget_category_id: BUDGET_CATEGORIES[3].id,
    vendor_id: "v0000000-0000-0000-0000-000000000003",
    description: "Jaipur Royal Lens Drone & 4K Teaser Token Booking",
    amount: "50000.00",
    currency: "INR",
    expense_date: "2026-11-01",
    status: "paid",
    created_by: USER_ID,
    created_at: "2026-11-01T13:00:00Z",
    updated_at: "2026-11-01T13:00:00Z",
  },
];

const BUDGET_SUMMARY = {
  currency: "INR",
  total_limit: "2500000.00",
  total_allocated: "2500000.00",
  unallocated_amount: "0.00",
  planned_expenses: "0.00",
  committed_expenses: "600000.00",
  paid_expenses: "600000.00",
  cancelled_expenses: "0.00",
  projected_total: "2500000.00",
  remaining_after_committed: "1900000.00",
  projected_headroom: "0.00",
  alerts: [
    "Palace deposit paid (₹4,00,000.00). Balance due 14 days before celebration.",
    "Catering initial commitment confirmed for 300 guests.",
  ],
  category_summaries: BUDGET_CATEGORIES.map((c) => ({
    category_id: c.id,
    category_key: c.category_key,
    name: c.name,
    planned_amount: c.planned_amount,
    committed_amount: c.committed_amount,
    paid_amount: c.paid_amount,
    projected_amount: c.projected_amount,
    remaining_amount: c.remaining_amount,
    is_over_budget: c.is_over_budget,
  })),
};

const TASKS = [
  {
    id: "t0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    function_id: null,
    title: "Finalize Royal Heritage Palace Contract",
    description: "Confirm Rambagh Palace ballroom and lawn bookings with event supervisor.",
    due_at: "2026-11-15T18:00:00Z",
    status: "done",
    priority: "urgent",
    assigned_user_id: USER_ID,
    origin: "manual",
    sort_order: 1,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    completed_at: "2026-11-01T10:30:00Z",
    depends_on_task_ids: [],
  },
  {
    id: "t0000000-0000-0000-0000-000000000002",
    event_id: EVENT_ID,
    function_id: null,
    title: "Select Royal Caterer & Approve 7-Course Menu",
    description: "Approve curated Rajasthani Dal Baati Churma, Ker Sangri, and European desserts.",
    due_at: "2026-11-20T18:00:00Z",
    status: "done",
    priority: "high",
    assigned_user_id: USER_ID,
    origin: "manual",
    sort_order: 2,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    completed_at: "2026-11-01T11:00:00Z",
    depends_on_task_ids: ["t0000000-0000-0000-0000-000000000001"],
  },
  {
    id: "t0000000-0000-0000-0000-000000000003",
    event_id: EVENT_ID,
    function_id: null,
    title: "Book Cinematographer & Drone Pilot Crew",
    description: "Confirm Jaipur Royal Lens for multi-camera 4K and pre-wedding shoot.",
    due_at: "2026-11-25T18:00:00Z",
    status: "done",
    priority: "high",
    assigned_user_id: USER_ID,
    origin: "manual",
    sort_order: 3,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    completed_at: "2026-11-01T12:00:00Z",
    depends_on_task_ids: [],
  },
  {
    id: "t0000000-0000-0000-0000-000000000004",
    event_id: EVENT_ID,
    function_id: null,
    title: "Dispatch Royal Wax-Sealed Invitations",
    description: "Deliver 300 bespoke invites with personalized gift boxes across India.",
    due_at: "2026-12-05T18:00:00Z",
    status: "in_progress",
    priority: "high",
    assigned_user_id: USER_ID,
    origin: "ai_accepted",
    sort_order: 4,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T14:00:00Z",
    completed_at: null,
    depends_on_task_ids: ["t0000000-0000-0000-0000-000000000001"],
  },
  {
    id: "t0000000-0000-0000-0000-000000000005",
    event_id: EVENT_ID,
    function_id: FUNCTIONS[1].id,
    title: "Sangeet Family Choreography Rehearsals",
    description: "Schedule 6 practice sessions for couple and cousin dance routines.",
    due_at: "2027-01-10T18:00:00Z",
    status: "todo",
    priority: "medium",
    assigned_user_id: USER_ID,
    origin: "ai_accepted",
    sort_order: 5,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    completed_at: null,
    depends_on_task_ids: [],
  },
  {
    id: "t0000000-0000-0000-0000-000000000006",
    event_id: EVENT_ID,
    function_id: FUNCTIONS[0].id,
    title: "Inspect Mehendi Sunshine Decor Setup",
    description: "Review flower arrangements, marigold canopies, and traditional seating.",
    due_at: "2027-02-11T12:00:00Z",
    status: "todo",
    priority: "medium",
    assigned_user_id: USER_ID,
    origin: "manual",
    sort_order: 6,
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T10:00:00Z",
    completed_at: null,
    depends_on_task_ids: ["t0000000-0000-0000-0000-000000000001"],
  },
];

const TIMELINE_SUMMARY = {
  total_tasks: 6,
  completed_tasks: 3,
  pending_tasks: 2,
  in_progress_tasks: 1,
  blocked_tasks: 0,
  cancelled_tasks: 0,
  overdue_tasks: 0,
  upcoming_tasks: 3,
  unscheduled_tasks: 0,
  high_priority_tasks: 3,
  completion_percentage: 50,
};

const VENDORS = [
  {
    id: "v0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    category: "venue",
    name: "Rambagh Palace Heritage Resort",
    contact_name: "Digvijay Singh Rathore",
    email: "events@rambaghpalace.taj.test",
    phone: "+91 141 238 5700",
    website_url: "https://tajhotels.com/rambagh-palace",
    notes: "Contracted for exclusive access to Mubarak Mahal and Kesar Bagh Lawns.",
    status: "booked",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T11:00:00Z",
    archived_at: null,
    quotes_count: 1,
    latest_quote_amount: "1000000.00",
    latest_quote_currency: "INR",
    associated_expenses_count: 1,
    total_spent_amount: "400000.00",
  },
  {
    id: "v0000000-0000-0000-0000-000000000002",
    event_id: EVENT_ID,
    category: "catering",
    name: "Rajputana Royal Gourmet Caterers",
    contact_name: "Chef Sanjeev Shekhawat",
    email: "chef@rajputanacatering.test",
    phone: "+91 98290 12345",
    website_url: "https://rajputanacatering.test",
    notes: "Shortlisted for royal banquet curation with 35 live artisan counters.",
    status: "shortlisted",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T12:00:00Z",
    archived_at: null,
    quotes_count: 1,
    latest_quote_amount: "700000.00",
    latest_quote_currency: "INR",
    associated_expenses_count: 1,
    total_spent_amount: "150000.00",
  },
  {
    id: "v0000000-0000-0000-0000-000000000003",
    event_id: EVENT_ID,
    category: "photography",
    name: "Jaipur Royal Lens Cinematography",
    contact_name: "Arjun & Priyanka Kothari",
    email: "hello@jaipurroyallens.test",
    phone: "+91 94140 67890",
    website_url: "https://jaipurroyallens.test",
    notes: "Contacted and token paid for 4K film teaser, drone coverage, and candid albums.",
    status: "booked",
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-01T13:00:00Z",
    archived_at: null,
    quotes_count: 1,
    latest_quote_amount: "250000.00",
    latest_quote_currency: "INR",
    associated_expenses_count: 1,
    total_spent_amount: "50000.00",
  },
];

const GIFTS = [
  {
    id: "g0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    title: "Dyson Airwrap Multi-Styler Complete Long",
    description: "Special Copper/Nickel Edition with travel pouch and styling attachments.",
    target_amount: "45900.00",
    currency: "INR",
    item_type: "physical",
    mode: "individual",
    priority: "high",
    external_url: "https://dyson.in/airwrap-multi-styler",
    image_url: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600",
    is_reserved: true,
    reserved_by_name: "Kabir & Ananya Verma",
    reservation_note: "So happy to celebrate you both! All our love.",
    contributed_amount: "45900.00",
    pledge_count: 1,
    status: "reserved",
    created_at: "2026-11-01T10:00:00Z",
  },
  {
    id: "g0000000-0000-0000-0000-000000000002",
    event_id: EVENT_ID,
    title: "Maldives Overwater Sunset Villa Honeymoon Fund",
    description: "5 nights in an overwater villa with private infinity pool and coral reef dive.",
    target_amount: "250000.00",
    currency: "INR",
    item_type: "experience",
    mode: "group",
    priority: "high",
    external_url: "https://maldives-resorts.example/honeymoon",
    image_url: "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=600",
    is_reserved: false,
    reserved_by_name: null,
    reservation_note: null,
    contributed_amount: "50000.00",
    pledge_count: 1,
    status: "active",
    created_at: "2026-11-01T10:00:00Z",
  },
];

const PUBLIC_REGISTRY = {
  registry_id: "r0000000-0000-0000-0000-000000000001",
  event_id: EVENT_ID,
  event_title: "Aarav & Meera's Jaipur Royal Wedding",
  couple_names: "Aarav Sharma & Meera Singhania",
  event_date: "2027-02-13",
  welcome_message: "Welcome to our wedding registry! Your presence and love are our greatest blessings. If you wish to gift, here are a few things we cherish for our new home and honeymoon.",
  is_public: true,
  share_token: SHARE_TOKEN,
  items: GIFTS,
};

const ADAPTIVE_PROPOSALS = [
  {
    id: "p0000000-0000-0000-0000-000000000001",
    event_id: EVENT_ID,
    title: "Increase Expected Guest Count from 300 to 350",
    change_request_text: "We need to add 50 more guests to our reception and pheras as extended family from abroad is attending.",
    status: "proposed",
    base_revision: 3,
    created_at: "2026-11-01T14:00:00Z",
    ai_explanation: "Expanding guest count by 50 attendees (+16.7%) impacts catering, invitation dispatches, and seating layouts. Rambagh Palace lawns safely accommodate up to 400 guests, so venue capacity is adequate. Catering budget requires an additional ₹1,75,000 INR based on ₹3,500/plate contracting rates.",
    impact_summary: {
      total_cost_delta: "+175000.00",
      currency: "INR",
      affected_modules: ["BudgetAI", "TimelineAI", "VendorConnect"],
      severity: "medium",
      capacity_status: "APPROVED (Within Rambagh Lawns 400-guest threshold)",
    },
    affected_records: [
      {
        module: "BudgetAI",
        entity_type: "category",
        entity_name: "Gourmet Royal Catering",
        change_nature: "Budget adjustment from ₹7,00,000 to ₹8,75,000 (+₹1,75,000 INR)",
      },
      {
        module: "TimelineAI",
        entity_type: "task",
        entity_name: "Dispatch Royal Wax-Sealed Invitations",
        change_nature: "Print run increased by 50 units (+7 days lead time)",
      },
      {
        module: "VendorConnect",
        entity_type: "vendor",
        entity_name: "Rajputana Royal Gourmet Caterers",
        change_nature: "Revised quotation request for 350 guests sent",
      },
    ],
  },
];

// ----------------- HTTP SERVER -----------------
const mockServer = http.createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:8000");
  const path = url.pathname.replace(/\/$/, "");

  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "*");
  res.setHeader("Content-Type", "application/json");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const send = (status, data) => {
    res.writeHead(status);
    res.end(JSON.stringify(data));
  };

  // Auth
  if (path === "/supabase/auth/v1/token") {
    return send(200, {
      access_token: "mock-access-token-123456",
      token_type: "bearer",
      expires_in: 3600,
      refresh_token: "mock-refresh-token",
      user: DEMO_USER,
    });
  }
  if (path === "/supabase/auth/v1/user") return send(200, DEMO_USER);

  // Meta & Me
  if (path === "/api/v1/health") return send(200, { status: "ok", service: "utsavai-api", version: "0.1.0" });
  if (path === "/api/v1/meta") return send(200, DEMO_META);
  if (path === "/api/v1/me") return send(200, DEMO_PROFILE);

  // Events
  if (path === "/api/v1/events") {
    if (req.method === "POST") return send(201, EVENT_DATA);
    return send(200, { data: [EVENT_DATA], next_cursor: null });
  }
  if (path === `/api/v1/events/${EVENT_ID}`) return send(200, EVENT_DATA);

  // Functions
  if (path === `/api/v1/events/${EVENT_ID}/functions`) {
    if (req.method === "POST") return send(201, FUNCTIONS[0]);
    return send(200, { items: FUNCTIONS });
  }

  // PlanAI
  if (path === `/api/v1/events/${EVENT_ID}/ai/conversations`) {
    return send(200, {
      items: [
        {
          id: "c0000000-0000-0000-0000-000000000001",
          event_id: EVENT_ID,
          user_id: USER_ID,
          title: "Jaipur Royal Wedding Schedule & Logistics",
          created_at: "2026-11-01T10:00:00Z",
          updated_at: "2026-11-01T14:00:00Z",
        },
      ],
    });
  }

  // Budget
  if (path === `/api/v1/events/${EVENT_ID}/budget`) return send(200, BUDGET);
  if (path === `/api/v1/events/${EVENT_ID}/budget/categories`) return send(200, BUDGET_CATEGORIES);
  if (path === `/api/v1/events/${EVENT_ID}/expenses`) return send(200, EXPENSES);
  if (path === `/api/v1/events/${EVENT_ID}/budget/summary`) return send(200, BUDGET_SUMMARY);

  // Timeline
  if (path === `/api/v1/events/${EVENT_ID}/tasks`) return send(200, TASKS);
  if (path === `/api/v1/events/${EVENT_ID}/tasks/summary`) return send(200, TIMELINE_SUMMARY);

  // Vendors
  if (path === `/api/v1/events/${EVENT_ID}/vendors`) return send(200, VENDORS);
  if (path === `/api/v1/events/${EVENT_ID}/vendors/summary`) {
    return send(200, {
      total_vendors: 3,
      booked_vendors: 2,
      shortlisted_vendors: 1,
      total_committed_quotes: "1950000.00",
      currency: "INR",
    });
  }

  // Gifts
  if (path === `/api/v1/events/${EVENT_ID}/gifts`) return send(200, GIFTS);
  if (path === `/api/v1/events/${EVENT_ID}/gifts/settings`) {
    return send(200, {
      share_token: SHARE_TOKEN,
      is_public: true,
      welcome_message: PUBLIC_REGISTRY.welcome_message,
    });
  }
  if (path === `/api/v1/public/registries/${SHARE_TOKEN}`) return send(200, PUBLIC_REGISTRY);

  // Adaptive
  if (path === `/api/v1/events/${EVENT_ID}/change-proposals`) return send(200, ADAPTIVE_PROPOSALS);
  if (path.endsWith("/change-proposals/interpret")) {
    return send(200, {
      summary: "Request to expand guest count from 300 to 350 for the Jaipur Royal celebration.",
      identified_changes: { expected_guest_count: 350 },
      confidence: 0.98,
    });
  }

  // Default fallback
  send(200, { status: "ok" });
});

await new Promise((resolve) => mockServer.listen(8000, "127.0.0.1", resolve));
console.log("Mock API server listening on http://127.0.0.1:8000");

// ----------------- NEXT.JS DEV SERVER -----------------
console.log("Starting Next.js frontend...");
const nextProc = spawn("npx.cmd", ["next", "dev", "--port", "3000"], {
  cwd: path.join(root, "apps", "web"),
  shell: true,
  env: {
    ...process.env,
    PORT: "3000",
    NEXT_PUBLIC_SUPABASE_URL: "http://localhost:8000/supabase",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "placeholder-anon-key-for-build-0000",
    NEXT_PUBLIC_APP_ENV: "development",
    API_BASE_URL: "http://localhost:8000",
  },
  stdio: "pipe",
});

await new Promise((resolve) => {
  nextProc.stdout.on("data", (d) => {
    const s = d.toString();
    if (s.includes("Ready") || s.includes("started") || s.includes("3000")) resolve();
  });
  // Fallback timeout after 10s
  setTimeout(resolve, 10000);
});
console.log("Next.js frontend is ready on http://localhost:3000");

// ----------------- RECORDING SEQUENCE -----------------
console.log("Launching Chromium for high-definition video recording (1440x900)...");
const browser = await chromium.launch({
  headless: true,
  args: ["--window-size=1440,900", "--disable-gpu"],
});

const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: {
    dir: recordingsDir,
    size: { width: 1440, height: 900 },
  },
});

const page = await context.newPage();

// Human-like smooth interaction helpers
const pause = (ms) => new Promise((res) => setTimeout(res, ms));

async function smoothScroll(p, yDistance, steps = 12) {
  for (let i = 0; i < steps; i++) {
    await p.mouse.wheel(0, yDistance / steps);
    await pause(80);
  }
}

async function typeRealistic(p, selector, text) {
  await p.click(selector);
  await p.fill(selector, "");
  for (const char of text) {
    await p.type(selector, char, { delay: 60 });
  }
}

console.log("🎬 Recording Step 1: Sign In");
await page.goto("http://localhost:3000/sign-in");
await pause(1500);
await typeRealistic(page, "input#email", "demo.host@utsavai.test");
await pause(600);
await typeRealistic(page, "input#password", "RoyalJaipur2027!");
await pause(800);
await page.click('button:has-text("Sign in")');

console.log("🎬 Recording Step 2: Dashboard");
await page.waitForURL("**/dashboard", { timeout: 15000 }).catch(() => {});
await pause(3000);
await smoothScroll(page, 300);
await pause(1500);
await smoothScroll(page, -300);
await pause(1500);

console.log("🎬 Recording Step 3: Create Wedding Workflow");
const createEventBtn = page.locator('a:has-text("Create event")').first();
if (await createEventBtn.isVisible()) {
  await createEventBtn.click();
  await page.waitForURL("**/events/new", { timeout: 8000 }).catch(() => {});
  await pause(2000);
  await typeRealistic(page, "input#title", "Aarav & Meera's Royal Celebration");
  await pause(800);
  await smoothScroll(page, 200);
  await pause(1200);
}

console.log("🎬 Recording Step 4: Event Workspace & PlanAI");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/plan-ai`);
await pause(3000);
await smoothScroll(page, 450);
await pause(2500);
await smoothScroll(page, -450);
await pause(1500);

console.log("🎬 Recording Step 5: BudgetAI Financial Intelligence");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/budget`);
await pause(3500);
await smoothScroll(page, 400);
await pause(2500);
await smoothScroll(page, 400);
await pause(2000);
await smoothScroll(page, -800);
await pause(1500);

console.log("🎬 Recording Step 6: TimelineAI Task Scheduling");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/timeline`);
await pause(3500);
await smoothScroll(page, 450);
await pause(2500);
await smoothScroll(page, -450);
await pause(1500);

console.log("🎬 Recording Step 7: VendorConnect Quotations & Management");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/vendors`);
await pause(3500);
await smoothScroll(page, 450);
await pause(2500);
await smoothScroll(page, -450);
await pause(1500);

console.log("🎬 Recording Step 8: GiftCircle Registry (Host Perspective)");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/giftcircle`);
await pause(3500);
await smoothScroll(page, 400);
await pause(2500);
await smoothScroll(page, -400);
await pause(1500);

console.log("🎬 Recording Step 9: Public Guest Gift Registry (/g/demo-jaipur-aarav-meera)");
await page.goto(`http://localhost:3000/g/${SHARE_TOKEN}`);
await pause(3500);
await smoothScroll(page, 450);
await pause(3000);
await smoothScroll(page, -450);
await pause(1500);

console.log("🎬 Recording Step 10: Adaptive Planning Engine (Cross-Module Replanning)");
await page.goto(`http://localhost:3000/events/${EVENT_ID}/adaptive`);
await pause(4000);
await smoothScroll(page, 400);
await pause(3000);
await smoothScroll(page, 400);
await pause(3000);
await smoothScroll(page, -800);
await pause(2500);

console.log("✨ Finalizing recording...");
const videoPath = await page.video().path();
await context.close();
await browser.close();

// Shutdown servers
nextProc.kill();
mockServer.close();

// Rename to standard presentation filename
const targetFile = path.join(recordingsDir, "utsavai_complete_demo.webm");
if (fs.existsSync(videoPath)) {
  fs.copyFileSync(videoPath, targetFile);
  console.log(`🎉 Demo screen recording saved successfully to: ${targetFile}`);
  console.log(`Video size: ${(fs.statSync(targetFile).size / (1024 * 1024)).toFixed(2)} MB`);
} else {
  console.log(`Video recorded at: ${videoPath}`);
}

process.exit(0);
