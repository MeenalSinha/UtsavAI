#!/usr/bin/env python3
"""UtsavAI High-Fidelity Standalone Demo Server.

Serves all required Supabase Auth and FastAPI v1 endpoints with complete,
rich demo data for 'Aarav & Meera's Jaipur Royal Wedding'.
Runs without external database dependencies for pristine screen recordings.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8000

EVENT_ID = "e0000000-0000-0000-0000-000000000001"
USER_ID = "d0000000-0000-0000-0000-000000000001"
USER_EMAIL = "demo.host@utsavai.test"
SHARE_TOKEN = "demo-jaipur-aarav-meera"

# ----------------- DEMO DATA -----------------

DEMO_USER = {
    "id": USER_ID,
    "user_id": USER_ID,
    "aud": "authenticated",
    "role": "authenticated",
    "email": USER_EMAIL,
    "email_confirmed_at": "2026-11-01T10:00:00Z",
    "display_name": "Aarav Sharma",
    "preferred_locale": "en-IN",
    "timezone": "Asia/Kolkata",
    "user_metadata": {"displayName": "Aarav Sharma"},
}

DEMO_PROFILE = {
    "user_id": USER_ID,
    "display_name": "Aarav Sharma",
    "preferred_locale": "en-IN",
    "timezone": "Asia/Kolkata",
    "email": USER_EMAIL,
}

DEMO_META = {
    "event_types": [
        {"key": "wedding", "label": "Wedding", "enabled": True},
        {"key": "reception", "label": "Reception", "enabled": True},
        {"key": "anniversary", "label": "Anniversary", "enabled": True},
    ],
    "default_event_type": "wedding",
    "currencies": ["INR", "USD", "EUR", "GBP"],
    "default_currency": "INR",
    "event_statuses": ["draft", "planning", "completed", "archived"],
    "patchable_statuses": ["draft", "planning", "completed"],
    "status_transitions": {
        "draft": ["planning", "archived"],
        "planning": ["completed", "archived"],
        "completed": ["archived"],
    },
    "locales": ["en-IN", "hi-IN", "en-US"],
    "default_locale": "en-IN",
    "default_timezone": "Asia/Kolkata",
    "default_country_code": "IN",
    "suggested_country_codes": ["IN", "AE", "US", "GB", "SG"],
    "limits": {"max_events_per_user": 20, "max_functions_per_event": 30},
}

EVENT_DATA = {
    "id": EVENT_ID,
    "event_type": "wedding",
    "title": "Aarav & Meera's Jaipur Royal Wedding",
    "start_at": "2027-02-12T10:00:00Z",
    "end_at": "2027-02-14T22:00:00Z",
    "timezone": "Asia/Kolkata",
    "location": {
        "name": "Rambagh Palace",
        "city": "Jaipur",
        "region": "Rajasthan",
        "country_code": "IN",
    },
    "expected_guest_count": 300,
    "currency": "INR",
    "status": "planning",
    "revision": 3,
    "created_at": "2026-11-01T10:00:00Z",
    "updated_at": "2026-11-01T14:30:00Z",
    "archived_at": None,
    "my_role": "owner",
}

FUNCTIONS = [
    {
        "id": "f0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "name": "Mehendi & Haldi Sunshine Ceremony",
        "starts_at": "2027-02-12T14:00:00Z",
        "ends_at": "2027-02-12T19:00:00Z",
        "location_name": "Kesar Bagh Lawns, Rambagh Palace",
        "notes": "Yellow and marigold floral themes. Live Rajasthani folk music.",
        "sort_order": 1,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
    },
    {
        "id": "f0000000-0000-0000-0000-000000000002",
        "event_id": EVENT_ID,
        "name": "Sangeet Extravaganza & Musical Night",
        "starts_at": "2027-02-12T19:30:00Z",
        "ends_at": "2027-02-13T01:00:00Z",
        "location_name": "Mubarak Mahal Grand Ballroom",
        "notes": "Choreographed family dance performances followed by DJ set.",
        "sort_order": 2,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
    },
    {
        "id": "f0000000-0000-0000-0000-000000000003",
        "event_id": EVENT_ID,
        "name": "Vedic Royal Wedding Pheras & Baraat",
        "starts_at": "2027-02-13T17:00:00Z",
        "ends_at": "2027-02-13T23:00:00Z",
        "location_name": "Royal Courtyard Mandap",
        "notes": "Grand royal elephant & vintage car Baraat arrival followed by twilight Pheras.",
        "sort_order": 3,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
    },
    {
        "id": "f0000000-0000-0000-0000-000000000004",
        "event_id": EVENT_ID,
        "name": "Grand Gala Reception & Royal Banquet",
        "starts_at": "2027-02-14T19:00:00Z",
        "ends_at": "2027-02-14T23:59:00Z",
        "location_name": "Maharani Gardens Palace Terrace",
        "notes": "Black-tie reception with 7-course royal Rajasthani and Continental feast.",
        "sort_order": 4,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
    },
]

BUDGET = {
    "id": "b0000000-0000-0000-0000-000000000001",
    "event_id": EVENT_ID,
    "total_limit": "2500000.00",
    "currency": "INR",
    "created_at": "2026-11-01T10:00:00Z",
    "updated_at": "2026-11-01T10:00:00Z",
}

BUDGET_CATEGORIES = [
    {
        "id": "c0000000-0000-0000-0000-000000000001",
        "budget_id": BUDGET["id"],
        "category_key": "venue",
        "name": "Palace Venue & Hospitality",
        "planned_amount": "1000000.00",
        "sort_order": 1,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "400000.00",
        "paid_amount": "400000.00",
        "projected_amount": "1000000.00",
        "remaining_amount": "600000.00",
        "is_over_budget": False,
    },
    {
        "id": "c0000000-0000-0000-0000-000000000002",
        "budget_id": BUDGET["id"],
        "category_key": "catering",
        "name": "Gourmet Royal Catering",
        "planned_amount": "700000.00",
        "sort_order": 2,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "150000.00",
        "paid_amount": "150000.00",
        "projected_amount": "700000.00",
        "remaining_amount": "550000.00",
        "is_over_budget": False,
    },
    {
        "id": "c0000000-0000-0000-0000-000000000003",
        "budget_id": BUDGET["id"],
        "category_key": "decor",
        "name": "Heritage Floral & Mandap Decor",
        "planned_amount": "300000.00",
        "sort_order": 3,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "0.00",
        "paid_amount": "0.00",
        "projected_amount": "300000.00",
        "remaining_amount": "300000.00",
        "is_over_budget": False,
    },
    {
        "id": "c0000000-0000-0000-0000-000000000004",
        "budget_id": BUDGET["id"],
        "category_key": "photography",
        "name": "Cinematography & Drone Photography",
        "planned_amount": "250000.00",
        "sort_order": 4,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "50000.00",
        "paid_amount": "50000.00",
        "projected_amount": "250000.00",
        "remaining_amount": "200000.00",
        "is_over_budget": False,
    },
    {
        "id": "c0000000-0000-0000-0000-000000000005",
        "budget_id": BUDGET["id"],
        "category_key": "entertainment",
        "name": "Sangeet Artists & Sound / Lights",
        "planned_amount": "150000.00",
        "sort_order": 5,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "0.00",
        "paid_amount": "0.00",
        "projected_amount": "150000.00",
        "remaining_amount": "150000.00",
        "is_over_budget": False,
    },
    {
        "id": "c0000000-0000-0000-0000-000000000006",
        "budget_id": BUDGET["id"],
        "category_key": "contingency",
        "name": "Contingency & Emergency Reserve",
        "planned_amount": "100000.00",
        "sort_order": 6,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "committed_amount": "0.00",
        "paid_amount": "0.00",
        "projected_amount": "100000.00",
        "remaining_amount": "100000.00",
        "is_over_budget": False,
    },
]

EXPENSES = [
    {
        "id": "x0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "budget_category_id": BUDGET_CATEGORIES[0]["id"],
        "vendor_id": "v0000000-0000-0000-0000-000000000001",
        "description": "Rambagh Palace 3-Day Venue Booking Advance Deposit",
        "amount": "400000.00",
        "currency": "INR",
        "expense_date": "2026-11-01",
        "status": "paid",
        "created_by": USER_ID,
        "created_at": "2026-11-01T11:00:00Z",
        "updated_at": "2026-11-01T11:00:00Z",
    },
    {
        "id": "x0000000-0000-0000-0000-000000000002",
        "event_id": EVENT_ID,
        "budget_category_id": BUDGET_CATEGORIES[1]["id"],
        "vendor_id": "v0000000-0000-0000-0000-000000000002",
        "description": "Rajputana Royal Caterers Menu Tasting & Chef Retainer",
        "amount": "150000.00",
        "currency": "INR",
        "expense_date": "2026-11-01",
        "status": "paid",
        "created_by": USER_ID,
        "created_at": "2026-11-01T12:00:00Z",
        "updated_at": "2026-11-01T12:00:00Z",
    },
    {
        "id": "x0000000-0000-0000-0000-000000000003",
        "event_id": EVENT_ID,
        "budget_category_id": BUDGET_CATEGORIES[3]["id"],
        "vendor_id": "v0000000-0000-0000-0000-000000000003",
        "description": "Jaipur Royal Lens Drone & 4K Teaser Token Booking",
        "amount": "50000.00",
        "currency": "INR",
        "expense_date": "2026-11-01",
        "status": "paid",
        "created_by": USER_ID,
        "created_at": "2026-11-01T13:00:00Z",
        "updated_at": "2026-11-01T13:00:00Z",
    },
]

BUDGET_SUMMARY = {
    "currency": "INR",
    "total_limit": "2500000.00",
    "total_allocated": "2500000.00",
    "unallocated_amount": "0.00",
    "planned_expenses": "0.00",
    "committed_expenses": "600000.00",
    "paid_expenses": "600000.00",
    "cancelled_expenses": "0.00",
    "projected_total": "2500000.00",
    "remaining_after_committed": "1900000.00",
    "projected_headroom": "0.00",
    "alerts": [
        "Palace deposit paid (₹4,00,000.00). Balance due 14 days before celebration.",
        "Catering initial commitment confirmed for 300 guests.",
    ],
    "category_summaries": [
        {
            "category_id": c["id"],
            "category_key": c["category_key"],
            "name": c["name"],
            "planned_amount": c["planned_amount"],
            "committed_amount": c["committed_amount"],
            "paid_amount": c["paid_amount"],
            "projected_amount": c["projected_amount"],
            "remaining_amount": c["remaining_amount"],
            "is_over_budget": c["is_over_budget"],
        }
        for c in BUDGET_CATEGORIES
    ],
}

TASKS = [
    {
        "id": "t0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "function_id": None,
        "title": "Finalize Royal Heritage Palace Contract",
        "description": "Confirm Rambagh Palace ballroom and lawn bookings with event supervisor.",
        "due_at": "2026-11-15T18:00:00Z",
        "status": "done",
        "priority": "urgent",
        "assigned_user_id": USER_ID,
        "origin": "manual",
        "sort_order": 1,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "completed_at": "2026-11-01T10:30:00Z",
        "depends_on_task_ids": [],
    },
    {
        "id": "t0000000-0000-0000-0000-000000000002",
        "event_id": EVENT_ID,
        "function_id": None,
        "title": "Select Royal Caterer & Approve 7-Course Menu",
        "description": "Approve curated Rajasthani Dal Baati Churma, Ker Sangri, and European desserts.",
        "due_at": "2026-11-20T18:00:00Z",
        "status": "done",
        "priority": "high",
        "assigned_user_id": USER_ID,
        "origin": "manual",
        "sort_order": 2,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "completed_at": "2026-11-01T11:00:00Z",
        "depends_on_task_ids": ["t0000000-0000-0000-0000-000000000001"],
    },
    {
        "id": "t0000000-0000-0000-0000-000000000003",
        "event_id": EVENT_ID,
        "function_id": None,
        "title": "Book Cinematographer & Drone Pilot Crew",
        "description": "Confirm Jaipur Royal Lens for multi-camera 4K and pre-wedding shoot.",
        "due_at": "2026-11-25T18:00:00Z",
        "status": "done",
        "priority": "high",
        "assigned_user_id": USER_ID,
        "origin": "manual",
        "sort_order": 3,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "completed_at": "2026-11-01T12:00:00Z",
        "depends_on_task_ids": [],
    },
    {
        "id": "t0000000-0000-0000-0000-000000000004",
        "event_id": EVENT_ID,
        "function_id": None,
        "title": "Dispatch Royal Wax-Sealed Invitations",
        "description": "Deliver 300 bespoke invites with personalized gift boxes across India.",
        "due_at": "2026-12-05T18:00:00Z",
        "status": "in_progress",
        "priority": "high",
        "assigned_user_id": USER_ID,
        "origin": "ai_accepted",
        "sort_order": 4,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T14:00:00Z",
        "completed_at": None,
        "depends_on_task_ids": ["t0000000-0000-0000-0000-000000000001"],
    },
    {
        "id": "t0000000-0000-0000-0000-000000000005",
        "event_id": EVENT_ID,
        "function_id": FUNCTIONS[1]["id"],
        "title": "Sangeet Family Choreography Rehearsals",
        "description": "Schedule 6 practice sessions for couple and cousin dance routines.",
        "due_at": "2027-01-10T18:00:00Z",
        "status": "todo",
        "priority": "medium",
        "assigned_user_id": USER_ID,
        "origin": "ai_accepted",
        "sort_order": 5,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "completed_at": None,
        "depends_on_task_ids": [],
    },
    {
        "id": "t0000000-0000-0000-0000-000000000006",
        "event_id": EVENT_ID,
        "function_id": FUNCTIONS[0]["id"],
        "title": "Inspect Mehendi Sunshine Decor Setup",
        "description": "Review flower arrangements, marigold canopies, and traditional seating.",
        "due_at": "2027-02-11T12:00:00Z",
        "status": "todo",
        "priority": "medium",
        "assigned_user_id": USER_ID,
        "origin": "manual",
        "sort_order": 6,
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T10:00:00Z",
        "completed_at": None,
        "depends_on_task_ids": ["t0000000-0000-0000-0000-000000000001"],
    },
]

TIMELINE_SUMMARY = {
    "total_tasks": 6,
    "completed_tasks": 3,
    "pending_tasks": 2,
    "in_progress_tasks": 1,
    "blocked_tasks": 0,
    "cancelled_tasks": 0,
    "overdue_tasks": 0,
    "upcoming_tasks": 3,
    "unscheduled_tasks": 0,
    "high_priority_tasks": 3,
    "completion_percentage": 50,
}

VENDORS = [
    {
        "id": "v0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "category": "venue",
        "name": "Rambagh Palace Heritage Resort",
        "contact_name": "Digvijay Singh Rathore",
        "email": "events@rambaghpalace.taj.test",
        "phone": "+91 141 238 5700",
        "website_url": "https://tajhotels.com/rambagh-palace",
        "notes": "Contracted for exclusive access to Mubarak Mahal and Kesar Bagh Lawns.",
        "status": "booked",
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T11:00:00Z",
        "archived_at": None,
        "quotes_count": 1,
        "latest_quote_amount": "1000000.00",
        "latest_quote_currency": "INR",
        "associated_expenses_count": 1,
        "total_spent_amount": "400000.00",
    },
    {
        "id": "v0000000-0000-0000-0000-000000000002",
        "event_id": EVENT_ID,
        "category": "catering",
        "name": "Rajputana Royal Gourmet Caterers",
        "contact_name": "Chef Sanjeev Shekhawat",
        "email": "chef@rajputanacatering.test",
        "phone": "+91 98290 12345",
        "website_url": "https://rajputanacatering.test",
        "notes": "Shortlisted for royal banquet curation with 35 live artisan counters.",
        "status": "shortlisted",
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T12:00:00Z",
        "archived_at": None,
        "quotes_count": 1,
        "latest_quote_amount": "700000.00",
        "latest_quote_currency": "INR",
        "associated_expenses_count": 1,
        "total_spent_amount": "150000.00",
    },
    {
        "id": "v0000000-0000-0000-0000-000000000003",
        "event_id": EVENT_ID,
        "category": "photography",
        "name": "Jaipur Royal Lens Cinematography",
        "contact_name": "Arjun & Priyanka Kothari",
        "email": "hello@jaipurroyallens.test",
        "phone": "+91 94140 67890",
        "website_url": "https://jaipurroyallens.test",
        "notes": "Contacted and token paid for 4K film teaser, drone coverage, and candid albums.",
        "status": "booked",
        "created_at": "2026-11-01T10:00:00Z",
        "updated_at": "2026-11-01T13:00:00Z",
        "archived_at": None,
        "quotes_count": 1,
        "latest_quote_amount": "250000.00",
        "latest_quote_currency": "INR",
        "associated_expenses_count": 1,
        "total_spent_amount": "50000.00",
    },
]

GIFTS = [
    {
        "id": "g0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "title": "Dyson Airwrap Multi-Styler Complete Long",
        "description": "Special Copper/Nickel Edition with travel pouch and styling attachments.",
        "target_amount": "45900.00",
        "currency": "INR",
        "item_type": "physical",
        "mode": "individual",
        "priority": "high",
        "external_url": "https://dyson.in/airwrap-multi-styler",
        "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600",
        "is_reserved": True,
        "reserved_by_name": "Kabir & Ananya Verma",
        "reservation_note": "So happy to celebrate you both! All our love.",
        "contributed_amount": "45900.00",
        "pledge_count": 1,
        "status": "reserved",
        "created_at": "2026-11-01T10:00:00Z",
    },
    {
        "id": "g0000000-0000-0000-0000-000000000002",
        "event_id": EVENT_ID,
        "title": "Maldives Overwater Sunset Villa Honeymoon Fund",
        "description": "5 nights in an overwater villa with private infinity pool and coral reef dive.",
        "target_amount": "250000.00",
        "currency": "INR",
        "item_type": "experience",
        "mode": "group",
        "priority": "high",
        "external_url": "https://maldives-resorts.example/honeymoon",
        "image_url": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=600",
        "is_reserved": False,
        "reserved_by_name": None,
        "reservation_note": None,
        "contributed_amount": "50000.00",
        "pledge_count": 1,
        "status": "active",
        "created_at": "2026-11-01T10:00:00Z",
    },
]

PUBLIC_REGISTRY = {
    "registry_id": "r0000000-0000-0000-0000-000000000001",
    "event_id": EVENT_ID,
    "event_title": "Aarav & Meera's Jaipur Royal Wedding",
    "couple_names": "Aarav Sharma & Meera Singhania",
    "event_date": "2027-02-13",
    "welcome_message": "Welcome to our wedding registry! Your presence and love are our greatest blessings. If you wish to gift, here are a few things we cherish for our new home and honeymoon.",
    "is_public": True,
    "share_token": SHARE_TOKEN,
    "items": GIFTS,
}

ADAPTIVE_PROPOSALS = [
    {
        "id": "p0000000-0000-0000-0000-000000000001",
        "event_id": EVENT_ID,
        "title": "Increase Expected Guest Count from 300 to 350",
        "change_request_text": "We need to add 50 more guests to our reception and pheras as extended family from abroad is attending.",
        "status": "proposed",
        "base_revision": 3,
        "created_at": "2026-11-01T14:00:00Z",
        "ai_explanation": "Expanding guest count by 50 attendees (+16.7%) impacts catering, invitation dispatches, and seating layouts. Rambagh Palace lawns safely accommodate up to 400 guests, so venue capacity is adequate. Catering budget requires an additional ₹1,75,000 INR based on ₹3,500/plate contracting rates.",
        "impact_summary": {
            "total_cost_delta": "+175000.00",
            "currency": "INR",
            "affected_modules": ["BudgetAI", "TimelineAI", "VendorConnect"],
            "severity": "medium",
            "capacity_status": "APPROVED (Within Rambagh Lawns 400-guest threshold)",
        },
        "affected_records": [
            {
                "module": "BudgetAI",
                "entity_type": "category",
                "entity_name": "Gourmet Royal Catering",
                "change_nature": "Budget adjustment from ₹7,00,000 to ₹8,75,000 (+₹1,75,000 INR)",
            },
            {
                "module": "TimelineAI",
                "entity_type": "task",
                "entity_name": "Dispatch Royal Wax-Sealed Invitations",
                "change_nature": "Print run increased by 50 units (+7 days lead time)",
            },
            {
                "module": "VendorConnect",
                "entity_type": "vendor",
                "entity_name": "Rajputana Royal Gourmet Caterers",
                "change_nature": "Revised quotation request for 350 guests sent",
            },
        ],
    }
]

# ----------------- HTTP REQUEST HANDLER -----------------


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging: suppress noisy per-request logs
        pass

    def _send_json(self, status: int, data: dict | list) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # 1. Supabase Auth
        if path == "/supabase/auth/v1/token":
            return self._send_json(
                200,
                {
                    "access_token": "mock-access-token-utsavai-123456",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "refresh_token": "mock-refresh-token",
                    "user": DEMO_USER,
                },
            )

        # 2. PlanAI Proposals Generate
        if "/ai/conversations" in path and path.endswith("/messages"):
            return self._send_json(
                200,
                {
                    "id": "m0000000-0000-0000-0000-000000000001",
                    "conversation_id": "c0000000-0000-0000-0000-000000000001",
                    "proposal_id": "prop-plan-001",
                    "role": "assistant",
                    "content": "I have created a majestic 3-day royal schedule at Rambagh Palace featuring Mehendi, Sangeet, Vedic Pheras, and Grand Reception with matching preparation milestones.",
                    "validation_status": "valid",
                    "created_at": "2026-11-01T14:00:00Z",
                },
            )

        # 3. Create Event
        if path == "/api/v1/events":
            new_event = dict(EVENT_DATA)
            new_event["title"] = payload.get("title", EVENT_DATA["title"])
            new_event["expected_guest_count"] = payload.get("expected_guest_count", 300)
            return self._send_json(201, new_event)

        # 4. Adaptive replanning proposal interpretation
        if path.endswith("/change-proposals/interpret"):
            return self._send_json(
                200,
                {
                    "summary": "Request to expand guest count from 300 to 350 for the Jaipur Royal celebration.",
                    "identified_changes": {
                        "expected_guest_count": 350,
                    },
                    "confidence": 0.98,
                },
            )

        # Default fallback for unhandled POST
        return self._send_json(200, {"status": "ok", "message": "action accepted"})

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path.rstrip("/")

        # 1. Supabase Auth User
        if path == "/supabase/auth/v1/user":
            return self._send_json(200, DEMO_USER)

        # 2. Health & Meta
        if path == "/api/v1/health":
            return self._send_json(200, {"status": "ok", "service": "utsavai-api", "version": "0.1.0"})
        if path == "/api/v1/meta":
            return self._send_json(200, DEMO_META)
        if path == "/api/v1/me":
            return self._send_json(200, DEMO_PROFILE)

        # 3. Events List & Detail
        if path == "/api/v1/events":
            return self._send_json(200, {"data": [EVENT_DATA], "next_cursor": None})
        if path == f"/api/v1/events/{EVENT_ID}":
            return self._send_json(200, EVENT_DATA)

        # 4. Functions
        if path == f"/api/v1/events/{EVENT_ID}/functions":
            return self._send_json(200, {"items": FUNCTIONS})

        # 5. PlanAI Conversations
        if path == f"/api/v1/events/{EVENT_ID}/ai/conversations":
            return self._send_json(
                200,
                {
                    "items": [
                        {
                            "id": "c0000000-0000-0000-0000-000000000001",
                            "event_id": EVENT_ID,
                            "user_id": USER_ID,
                            "title": "Jaipur Royal Wedding Schedule & Logistics",
                            "created_at": "2026-11-01T10:00:00Z",
                            "updated_at": "2026-11-01T14:00:00Z",
                        }
                    ]
                },
            )

        # 6. BudgetAI
        if path == f"/api/v1/events/{EVENT_ID}/budget":
            return self._send_json(200, BUDGET)
        if path == f"/api/v1/events/{EVENT_ID}/budget/categories":
            return self._send_json(200, BUDGET_CATEGORIES)
        if path == f"/api/v1/events/{EVENT_ID}/expenses":
            return self._send_json(200, EXPENSES)
        if path == f"/api/v1/events/{EVENT_ID}/budget/summary":
            return self._send_json(200, BUDGET_SUMMARY)

        # 7. TimelineAI
        if path == f"/api/v1/events/{EVENT_ID}/tasks":
            return self._send_json(200, TASKS)
        if path == f"/api/v1/events/{EVENT_ID}/tasks/summary":
            return self._send_json(200, TIMELINE_SUMMARY)

        # 8. VendorConnect
        if path == f"/api/v1/events/{EVENT_ID}/vendors":
            return self._send_json(200, VENDORS)
        if path == f"/api/v1/events/{EVENT_ID}/vendors/summary":
            return self._send_json(
                200,
                {
                    "total_vendors": 3,
                    "booked_vendors": 2,
                    "shortlisted_vendors": 1,
                    "total_committed_quotes": "1950000.00",
                    "currency": "INR",
                },
            )

        # 9. GiftCircle
        if path == f"/api/v1/events/{EVENT_ID}/gifts":
            return self._send_json(200, GIFTS)
        if path == f"/api/v1/events/{EVENT_ID}/gifts/settings":
            return self._send_json(
                200,
                {
                    "share_token": SHARE_TOKEN,
                    "is_public": True,
                    "welcome_message": PUBLIC_REGISTRY["welcome_message"],
                },
            )
        if path == f"/api/v1/public/registries/{SHARE_TOKEN}":
            return self._send_json(200, PUBLIC_REGISTRY)

        # 10. Adaptive Planning Engine
        if path == f"/api/v1/events/{EVENT_ID}/change-proposals":
            return self._send_json(200, ADAPTIVE_PROPOSALS)

        # Catch-all
        return self._send_json(200, {})


def run():
    server = HTTPServer((HOST, PORT), MockHandler)
    print(f"UtsavAI Demo Server running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
