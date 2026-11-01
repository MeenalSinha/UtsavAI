"""Central application rules: categories, statuses, roles, permissions, defaults.

Every other module imports from here. The same values are published to the
frontend through GET /api/v1/meta so the two sides cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class EventTypeConfig:
    key: str
    label: str
    enabled: bool


# Event categories are configuration, never a database enum (docs/DATABASE_SCHEMA.md 13).
EVENT_TYPES: tuple[EventTypeConfig, ...] = (
    EventTypeConfig("wedding", "Wedding", True),
    EventTypeConfig("birthday", "Birthday", False),
    EventTypeConfig("anniversary", "Anniversary", False),
    EventTypeConfig("community", "Community event", False),
)
ENABLED_EVENT_TYPES: frozenset[str] = frozenset(t.key for t in EVENT_TYPES if t.enabled)

DEFAULT_EVENT_TYPE = "wedding"
SUPPORTED_CURRENCIES: tuple[str, ...] = ("INR", "USD", "EUR", "GBP", "AED", "SGD", "AUD", "CAD")
DEFAULT_CURRENCY = "INR"
DEFAULT_COUNTRY_CODE = "IN"
DEFAULT_TIMEZONE = "Asia/Kolkata"
SUPPORTED_LOCALES: tuple[str, ...] = ("en-IN", "en-US", "en-GB", "hi-IN")
DEFAULT_LOCALE = "en-IN"

# Suggestions for the UI country picker. The API accepts any ISO 3166-1 alpha-2 code.
SUGGESTED_COUNTRY_CODES: tuple[str, ...] = (
    "IN", "US", "GB", "AE", "SG", "AU", "CA", "DE", "FR", "NZ", "MY", "ZA", "NP", "LK", "BD",
)  # fmt: skip

MAX_TITLE_LENGTH = 160
MAX_LOCATION_NAME_LENGTH = 160
MAX_LOCATION_PART_LENGTH = 120
MAX_DISPLAY_NAME_LENGTH = 80
MAX_GUEST_COUNT = 100_000


class EventStatus(StrEnum):
    DRAFT = "draft"
    PLANNING = "planning"
    COMPLETED = "completed"
    ARCHIVED = "archived"


DEFAULT_EVENT_STATUS = EventStatus.DRAFT

# Documented lifecycle. "archived" is reached only through DELETE /events/{id}
# and is terminal in Phase 1 (restore is out of scope).
STATUS_TRANSITIONS: dict[EventStatus, frozenset[EventStatus]] = {
    EventStatus.DRAFT: frozenset({EventStatus.PLANNING}),
    EventStatus.PLANNING: frozenset({EventStatus.DRAFT, EventStatus.COMPLETED}),
    EventStatus.COMPLETED: frozenset({EventStatus.PLANNING}),
    EventStatus.ARCHIVED: frozenset(),
}
PATCHABLE_STATUSES: frozenset[EventStatus] = frozenset(
    {EventStatus.DRAFT, EventStatus.PLANNING, EventStatus.COMPLETED}
)


class MemberRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class MemberStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    REVOKED = "revoked"


class Permission(StrEnum):
    EVENT_READ = "event.read"
    EVENT_UPDATE = "event.update"
    EVENT_ARCHIVE = "event.archive"
    MEMBER_MANAGE = "member.manage"
    PREFERENCE_MANAGE = "preference.manage"
    FUNCTION_MANAGE = "function.manage"
    PLAN_GENERATE = "plan.generate"
    PLAN_ACCEPT = "plan.accept"
    BUDGET_READ = "budget.read"
    BUDGET_MANAGE = "budget.manage"
    EXPENSE_READ = "expense.read"
    EXPENSE_MANAGE = "expense.manage"
    TASK_READ = "task.read"
    TASK_MANAGE = "task.manage"
    BUDGET_PROPOSE = "budget.propose"
    TIMELINE_PROPOSE = "timeline.propose"
    VENDOR_READ = "vendor.read"
    VENDOR_MANAGE = "vendor.manage"
    GIFT_REGISTRY_READ = "gift_registry.read"
    GIFT_REGISTRY_MANAGE = "gift_registry.manage"


ROLE_PERMISSIONS: dict[MemberRole, frozenset[Permission]] = {
    MemberRole.OWNER: frozenset(Permission),
    MemberRole.EDITOR: frozenset(
        {
            Permission.EVENT_READ,
            Permission.EVENT_UPDATE,
            Permission.PREFERENCE_MANAGE,
            Permission.FUNCTION_MANAGE,
            Permission.PLAN_GENERATE,
            Permission.PLAN_ACCEPT,
            Permission.BUDGET_READ,
            Permission.BUDGET_MANAGE,
            Permission.EXPENSE_READ,
            Permission.EXPENSE_MANAGE,
            Permission.TASK_READ,
            Permission.TASK_MANAGE,
            Permission.BUDGET_PROPOSE,
            Permission.TIMELINE_PROPOSE,
            Permission.VENDOR_READ,
            Permission.VENDOR_MANAGE,
            Permission.GIFT_REGISTRY_READ,
            Permission.GIFT_REGISTRY_MANAGE,
        }
    ),
    MemberRole.VIEWER: frozenset(
        {
            Permission.EVENT_READ,
            Permission.BUDGET_READ,
            Permission.EXPENSE_READ,
            Permission.TASK_READ,
            Permission.VENDOR_READ,
            Permission.GIFT_REGISTRY_READ,
        }
    ),
}


class VendorStatus(StrEnum):
    IDENTIFIED = "identified"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    SHORTLISTED = "shortlisted"
    BOOKED = "booked"
    DECLINED = "declined"


class QuoteStatus(StrEnum):
    RECEIVED = "received"
    SHORTLISTED = "shortlisted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class GiftItemType(StrEnum):
    PRODUCT = "product"
    CASH_FUND = "cash_fund"
    EXPERIENCE = "experience"
    OTHER = "other"


class GiftMode(StrEnum):
    INDIVIDUAL = "individual"
    GROUP = "group"


class GiftItemPriority(StrEnum):
    NICE_TO_HAVE = "nice_to_have"
    IMPORTANT = "important"
    HIGH_PRIORITY = "high_priority"


class GiftReservationStatus(StrEnum):
    RESERVED = "reserved"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"


class GiftContributionStatus(StrEnum):
    PLEDGED = "pledged"
    VERIFIED = "verified"
    WITHDRAWN = "withdrawn"
    REFUNDED = "refunded"


class VerificationMethod(StrEnum):
    HOST_MANUAL_CONFIRMATION = "host_manual_confirmation"
    PAYMENT_PROVIDER_WEBHOOK = "payment_provider_webhook"


class ProposalStatus(StrEnum):
    PROPOSED = "proposed"
    PARTIALLY_ACCEPTED = "partially_accepted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    STALE = "stale"


class ProposalType(StrEnum):
    PLAN = "plan"
    BUDGET_SUGGESTIONS = "budget_suggestions"
    TIMELINE = "timeline"


class ExpenseStatus(StrEnum):
    PLANNED = "planned"
    COMMITTED = "committed"
    PAID = "paid"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskOrigin(StrEnum):
    MANUAL = "manual"
    AI_ACCEPTED = "ai_accepted"
    ADAPTIVE_ACCEPTED = "adaptive_accepted"


DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class EventSort(StrEnum):
    START_ASC = "start_at"
    CREATED_DESC = "created_at"


def role_allows(role: MemberRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
