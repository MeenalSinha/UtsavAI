"""UtsavAI isolated synthetic demo environment seeding and cleanup script.

Seeds a comprehensive, realistic 3-day Jaipur Indian wedding across all six modules:
- Core Event Planning & PlanAI (3-day multi-function royal celebration)
- BudgetAI (Deterministic INR category allocations and tracked expenses)
- TimelineAI (DAG tasks with topological dependencies)
- VendorConnect (Multiple vendor quotes and comparison metrics)
- GiftCircle (Registry with individual and group gifting items + pledges)
- Adaptive Planning Engine (A candidate change proposal with calculated downstream impact)

Usage:
    uv run python scripts/seed_demo_data.py
    uv run python scripts/seed_demo_data.py --clean
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add apps/api to path so we can import models and settings
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

import psycopg
from app.core.config import get_settings
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_demo")

DEMO_USER_ID = uuid.UUID("d0000000-0000-0000-0000-000000000001")
DEMO_EVENT_ID = uuid.UUID("e0000000-0000-0000-0000-000000000001")
DEMO_EMAIL = "demo.host@utsavai.test"
DEMO_SHARE_TOKEN = "demo-jaipur-aarav-meera"  # noqa: S105
DEMO_TOKEN_HASH = hashlib.sha256(DEMO_SHARE_TOKEN.encode("utf-8")).hexdigest()


def get_connection(admin_url: str | None = None) -> psycopg.Connection[Any]:
    settings = get_settings()
    conninfo = admin_url or settings.database_url.get_secret_value()
    return psycopg.connect(conninfo, row_factory=dict_row, autocommit=False)


def clean_demo_data(conn: psycopg.Connection[Any]) -> None:
    logger.info("Cleaning demo data for user %s and event %s...", DEMO_USER_ID, DEMO_EVENT_ID)
    with conn.cursor() as cur:
        # Cascades handle most relationships through foreign keys
        cur.execute("DELETE FROM public.events WHERE id = %s", (DEMO_EVENT_ID,))
        cur.execute("DELETE FROM public.profiles WHERE id = %s", (DEMO_USER_ID,))
    conn.commit()
    logger.info("Demo data cleaned successfully.")


def seed_demo_data(conn: psycopg.Connection[Any]) -> None:
    logger.info("Seeding synthetic 3-day Jaipur Royal Wedding demo...")
    now = datetime.datetime.now(datetime.UTC)
    day1_start = now + datetime.timedelta(days=45)
    day1_end = day1_start + datetime.timedelta(hours=5)
    day2_start = now + datetime.timedelta(days=46)
    day2_end = day2_start + datetime.timedelta(hours=6)
    day3_start = now + datetime.timedelta(days=47)
    day3_end = day3_start + datetime.timedelta(hours=5)

    with conn.cursor() as cur:
        # 1. Host Profile
        cur.execute(
            """
            INSERT INTO public.profiles (id, email, display_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name
            """,
            (DEMO_USER_ID, DEMO_EMAIL, "Aarav Sharma & Meera Rathore", now, now),
        )

        # 2. Main Event
        cur.execute(
            """
            INSERT INTO public.events (
                id, owner_id, title, event_type, city, state, country,
                start_date, end_date, expected_guest_count, total_budget,
                currency, primary_contact_phone, status, revision, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                total_budget = EXCLUDED.total_budget,
                expected_guest_count = EXCLUDED.expected_guest_count
            """,
            (
                DEMO_EVENT_ID,
                DEMO_USER_ID,
                "Aarav & Meera's Jaipur Royal Wedding",
                "wedding",
                "Jaipur",
                "Rajasthan",
                "India",
                day1_start.date(),
                day3_start.date(),
                300,
                Decimal("2500000.00"),
                "INR",
                "+91 98765 43210",
                "planning",
                1,
                now,
                now,
            ),
        )

        # 3. Event Members (Owner)
        cur.execute(
            """
            INSERT INTO public.event_members (event_id, user_id, role, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (event_id, user_id) DO NOTHING
            """,
            (DEMO_EVENT_ID, DEMO_USER_ID, "owner", now),
        )

        # 4. Event Functions (PlanAI)
        functions = [
            (
                uuid.UUID("f0000000-0000-0000-0000-000000000001"),
                "Mehendi & Haldi Sunshine Ceremony",
                "mehendi",
                day1_start,
                day1_end,
                "Courtyard Lawns, Rambagh Palace, Jaipur",
                180,
                1,
            ),
            (
                uuid.UUID("f0000000-0000-0000-0000-000000000002"),
                "Sangeet Extravaganza & Musical Night",
                "sangeet",
                day1_end + datetime.timedelta(hours=3),
                day1_end + datetime.timedelta(hours=8),
                "Grand Ballroom, Rambagh Palace, Jaipur",
                280,
                2,
            ),
            (
                uuid.UUID("f0000000-0000-0000-0000-000000000003"),
                "Vedic Royal Wedding Pheras & Baraat",
                "wedding_ceremony",
                day2_start,
                day2_end,
                "Mughal Amphitheatre, Rambagh Palace, Jaipur",
                300,
                3,
            ),
            (
                uuid.UUID("f0000000-0000-0000-0000-000000000004"),
                "Grand Gala Reception & Dinner",
                "reception",
                day3_start,
                day3_end,
                "Palace Poolside Pavilion, Rambagh Palace, Jaipur",
                300,
                4,
            ),
        ]
        for fid, fname, ftype, fstart, fend, floc, fguests, fsort in functions:
            cur.execute(
                """
                INSERT INTO public.event_functions (
                    id, event_id, name, function_type, starts_at, ends_at,
                    location, expected_guest_count, sort_order, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                (
                    fid,
                    DEMO_EVENT_ID,
                    fname,
                    ftype,
                    fstart,
                    fend,
                    floc,
                    fguests,
                    fsort,
                    now,
                    now,
                ),
            )

        # 5. BudgetAI: Categories & Expenses
        categories = [
            (
                uuid.UUID("b0000000-0000-0000-0000-000000000001"),
                "Venue & Accommodation",
                Decimal("800000.00"),
            ),
            (
                uuid.UUID("b0000000-0000-0000-0000-000000000002"),
                "Royal Catering & Dining",
                Decimal("750000.00"),
            ),
            (
                uuid.UUID("b0000000-0000-0000-0000-000000000003"),
                "Decor, Flowers & Production",
                Decimal("450000.00"),
            ),
            (
                uuid.UUID("b0000000-0000-0000-0000-000000000004"),
                "Photography & Cinematography",
                Decimal("250000.00"),
            ),
            (
                uuid.UUID("b0000000-0000-0000-0000-000000000005"),
                "Entertainment & Live Artists",
                Decimal("250000.00"),
            ),
        ]
        for cid, cname, camount in categories:
            cur.execute(
                """
                INSERT INTO public.budget_categories (
                    id, event_id, name, allocated_amount, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET allocated_amount = EXCLUDED.allocated_amount
                """,
                (cid, DEMO_EVENT_ID, cname, camount, now, now),
            )

        # Expenses
        expenses = [
            (
                uuid.UUID("e1000000-0000-0000-0000-000000000001"),
                categories[0][0],
                "Palace Booking Advance Deposit (50%)",
                Decimal("400000.00"),
                "paid",
            ),
            (
                uuid.UUID("e1000000-0000-0000-0000-000000000002"),
                categories[1][0],
                "Catering Menu Tasting & Ingredient Reservation",
                Decimal("150000.00"),
                "paid",
            ),
            (
                uuid.UUID("e1000000-0000-0000-0000-000000000003"),
                categories[3][0],
                "Pre-Wedding Drone & Teaser Shoot Token",
                Decimal("50000.00"),
                "paid",
            ),
        ]
        for eid, cid, ename, eamount, estatus in expenses:
            cur.execute(
                """
                INSERT INTO public.expenses (
                    id, event_id, category_id, title, amount, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET amount = EXCLUDED.amount
                """,
                (eid, DEMO_EVENT_ID, cid, ename, eamount, estatus, now, now),
            )

        # 6. TimelineAI: Tasks and Dependencies
        tasks = [
            (
                uuid.UUID("t0000000-0000-0000-0000-000000000001"),
                "Finalize Palace Banquet & Mandap Contract",
                day1_start - datetime.timedelta(days=30),
                "completed",
            ),
            (
                uuid.UUID("t0000000-0000-0000-0000-000000000002"),
                "Approve Royal Rajputana Theme & Floral Layouts",
                day1_start - datetime.timedelta(days=20),
                "in_progress",
            ),
            (
                uuid.UUID("t0000000-0000-0000-0000-000000000003"),
                "Curate 7-Course Royal Rajasthani Banquet Tasting Menu",
                day1_start - datetime.timedelta(days=15),
                "todo",
            ),
        ]
        for tid, ttitle, tdue, tstatus in tasks:
            cur.execute(
                """
                INSERT INTO public.tasks (
                    id, event_id, title, due_date, status, priority, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title
                """,
                (tid, DEMO_EVENT_ID, ttitle, tdue, tstatus, "high", now, now),
            )

        # 7. VendorConnect: Vendors & Quotations
        vendors = [
            (
                uuid.UUID("v0000000-0000-0000-0000-000000000001"),
                "Rambagh Palace Heritage Venues",
                "venue",
                "events@rambagh.palace.test",
                "+91 141 2385700",
            ),
            (
                uuid.UUID("v0000000-0000-0000-0000-000000000002"),
                "Rajputana Royal Feast Caterers",
                "catering",
                "feasts@rajputanacatering.test",
                "+91 98290 11223",
            ),
            (
                uuid.UUID("v0000000-0000-0000-0000-000000000003"),
                "Jaipur Royal Lens & Cinema",
                "photography",
                "studio@jaipurroyallens.test",
                "+91 94140 55667",
            ),
        ]
        for vid, vname, vcat, vemail, vphone in vendors:
            cur.execute(
                """
                INSERT INTO public.vendors (
                    id, event_id, name, category, contact_email, contact_phone, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                (vid, DEMO_EVENT_ID, vname, vcat, vemail, vphone, now, now),
            )

        # Quotations
        quotes = [
            (
                uuid.UUID("q0000000-0000-0000-0000-000000000001"),
                vendors[0][0],
                Decimal("800000.00"),
                "accepted",
                "Exclusive 3-day access to Courtyard Lawns, Grand Ballroom, and Amphitheatre.",
            ),
            (
                uuid.UUID("q0000000-0000-0000-0000-000000000002"),
                vendors[1][0],
                Decimal("720000.00"),
                "accepted",
                "All-inclusive 4-event banqueting with live dessert stations and mocktail counters.",
            ),
            (
                uuid.UUID("q0000000-0000-0000-0000-000000000003"),
                vendors[2][0],
                Decimal("240000.00"),
                "accepted",
                (
                    "Comprehensive 4K cinematography, drone pilot, 2 candid photographers, "
                    "and hardcover albums."
                ),
            ),
        ]
        for qid, vid, qamount, qstatus, qnotes in quotes:
            cur.execute(
                """
                INSERT INTO public.vendor_quotations (
                    id, event_id, vendor_id, total_amount, status, notes, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET total_amount = EXCLUDED.total_amount
                """,
                (qid, DEMO_EVENT_ID, vid, qamount, qstatus, qnotes, now, now),
            )

        # 8. GiftCircle: Registry & Items
        reg_id = uuid.UUID("g0000000-0000-0000-0000-000000000001")
        cur.execute(
            """
            INSERT INTO public.gift_registries (
                id, event_id, title, description, share_token, share_token_hash,
                is_active, expires_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title
            """,
            (
                reg_id,
                DEMO_EVENT_ID,
                "Aarav & Meera's Wedding Gift Registry",
                (
                    "Your love and blessings are our greatest gift. "
                    "If you wish to contribute, explore our registry."
                ),
                DEMO_SHARE_TOKEN,
                DEMO_TOKEN_HASH,
                True,
                day3_end + datetime.timedelta(days=14),
                now,
                now,
            ),
        )

        # Registry Items
        gift_items = [
            (
                uuid.UUID("g1000000-0000-0000-0000-000000000001"),
                reg_id,
                "Dyson Airwrap Multi-Styler Complete Long",
                "For Meera's styling kit",
                Decimal("48900.00"),
                "individual",
                "reserved",
                "Kabir & Ananya Verma",
            ),
            (
                uuid.UUID("g1000000-0000-0000-0000-000000000002"),
                reg_id,
                "Soneva Jani Overwater Villa Maldives Honeymoon Fund",
                "Group gift fund towards our dream 5-night overwater villa experience",
                Decimal("250000.00"),
                "group",
                "available",
                None,
            ),
            (
                uuid.UUID("g1000000-0000-0000-0000-000000000003"),
                reg_id,
                "De'Longhi Magnifica S Espresso Machine",
                "For our cozy morning coffee ritual",
                Decimal("54000.00"),
                "individual",
                "available",
                None,
            ),
        ]
        for gid, grid, gtitle, gdesc, gprice, gtype, gstatus, gres in gift_items:
            cur.execute(
                """
                INSERT INTO public.gift_items (
                    id, registry_id, title, description, target_price,
                    gift_type, status, reserved_by_name, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET target_price = EXCLUDED.target_price
                """,
                (gid, grid, gtitle, gdesc, gprice, gtype, gstatus, gres, now, now),
            )

        # Group gift pledge
        cur.execute(
            """
            INSERT INTO public.gift_contributions (
                id, item_id, contributor_name, contributor_email, amount,
                status, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                uuid.UUID("c0000000-0000-0000-0000-000000000001"),
                gift_items[1][0],
                "Rohan Singhal & Family",
                "rohan.singhal@example.test",
                Decimal("50000.00"),
                "verified",
                "Wishing you a lifetime of joy in paradise!",
                now,
                now,
            ),
        )

        # 9. Adaptive Planning: Sample Proposal
        prop_id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
        impact_sample = {
            "summary": "Increasing guest count from 300 to 350 requires catering budget expansion.",
            "impacts": [
                {
                    "module": "budget",
                    "severity": "medium",
                    "message": (
                        "Catering per-plate allocation projected to increase by ₹1,20,000 "
                        "for 50 additional guests."
                    ),
                    "details": {
                        "previous_guests": 300,
                        "new_guests": 350,
                        "estimated_addition": 120000,
                    },
                },
                {
                    "module": "timeline",
                    "severity": "low",
                    "message": "Seating chart task deadline should be reviewed to accommodate extra seating.",
                    "details": {"action": "flag_review"},
                },
            ],
            "warnings": [
                (
                    "Palace Amphitheatre has a certified maximum capacity of 380 guests. "
                    "350 guests is near the threshold."
                )
            ],
            "suggested_options": [
                {
                    "id": "opt_flag_budget",
                    "title": "Flag Catering Category for Budget Adjustment",
                    "description": "Mark the Royal Catering budget allocation for review.",
                    "operations": [
                        {
                            "op_code": "op_flag_budget_for_review",
                            "target_module": "budget",
                            "payload": {"reason": "Guest count expansion to 350"},
                        }
                    ],
                }
            ],
        }

        cur.execute(
            """
            INSERT INTO public.change_proposals (
                id, event_id, created_by_user_id, base_revision, request_text,
                event_changes, function_changes, impact_analysis, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status
            """,
            (
                prop_id,
                DEMO_EVENT_ID,
                DEMO_USER_ID,
                1,
                "Accommodate 50 additional close family relatives across all ceremonies",
                json.dumps({"expected_guest_count": 350}),
                json.dumps([]),
                json.dumps(impact_sample),
                "proposed",
                now,
                now,
            ),
        )

    conn.commit()
    logger.info("Demo environment successfully seeded!")
    logger.info("  Event ID: %s", DEMO_EVENT_ID)
    logger.info("  Host User: %s (%s)", DEMO_EMAIL, DEMO_USER_ID)
    logger.info("  Public Registry Token: %s", DEMO_SHARE_TOKEN)
    logger.info("  Public Registry URL: /g/%s", DEMO_SHARE_TOKEN)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or clean UtsavAI synthetic demo environment.")
    parser.add_argument("--clean", action="store_true", help="Remove synthetic demo records.")
    parser.add_argument("--admin-url", type=str, default=None, help="PostgreSQL connection string.")
    args = parser.parse_args()

    conn = get_connection(args.admin_url)
    try:
        if args.clean:
            clean_demo_data(conn)
        else:
            seed_demo_data(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
