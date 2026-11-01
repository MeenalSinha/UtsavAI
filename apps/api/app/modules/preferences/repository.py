"""Persistence for event preferences."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.database.pool import Connection


def get_preferences(conn: Connection, event_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        """
        select event_id, style_tags, cultural_context, priorities,
               accessibility_notes, schema_version, updated_at
          from public.event_preferences
         where event_id = %s
        """,
        (event_id,),
    ).fetchone()
    return dict(row) if row else None


def upsert_preferences(conn: Connection, event_id: uuid.UUID, values: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(
        """
        insert into public.event_preferences
          (event_id, style_tags, cultural_context, priorities, accessibility_notes, schema_version)
        values
          (%(event_id)s, %(style_tags)s, %(cultural_context)s, %(priorities)s,
           %(accessibility_notes)s, %(schema_version)s)
        on conflict (event_id) do update set
          style_tags = excluded.style_tags,
          cultural_context = excluded.cultural_context,
          priorities = excluded.priorities,
          accessibility_notes = excluded.accessibility_notes,
          schema_version = excluded.schema_version,
          updated_at = now()
        returning event_id, style_tags, cultural_context, priorities,
                  accessibility_notes, schema_version, updated_at
        """,
        {
            "event_id": event_id,
            "style_tags": values["style_tags"],
            "cultural_context": json.dumps(values["cultural_context"]),
            "priorities": json.dumps(values["priorities"]),
            "accessibility_notes": json.dumps(values["accessibility_notes"]),
            "schema_version": values.get("schema_version", 1),
        },
    ).fetchone()
    assert row is not None
    return dict(row)
