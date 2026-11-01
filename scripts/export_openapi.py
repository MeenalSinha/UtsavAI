"""Writes the generated OpenAPI schema to apps/web/openapi.json (used by the TS contract check)."""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://utsavai_app:placeholder@localhost:5432/utsavai")
os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.config import get_settings  # noqa: E402
from app.database.pool import Database  # noqa: E402
from app.main import create_app  # noqa: E402

settings = get_settings()
schema = create_app(settings, database=Database(settings)).openapi()
target = ROOT / "apps" / "web" / "openapi.json"
with open(target, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(schema, indent=2, sort_keys=True) + "\n")
print(f"wrote {target}")
