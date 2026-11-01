"""Apply all migrations in supabase/migrations/*.sql to a PostgreSQL database."""

import os
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"


def run_migrations(admin_url: str) -> None:
    print("Connecting to database...")
    with psycopg.connect(admin_url, autocommit=True) as conn:
        print("Connected.")
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        print(f"Found {len(sql_files)} migration files.")

        for f in sql_files:
            print(f"Applying: {f.name}...")
            content = f.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(content)
            print(f" -> OK: {f.name}")

        print("Enabling login for utsavai_app runtime role...")
        app_password = os.environ.get("UTSAVAI_APP_PASSWORD", "UtsavAiApp2026SecurePass!")
        with conn.cursor() as cur:
            cur.execute(f"ALTER ROLE utsavai_app WITH LOGIN PASSWORD '{app_password}';")
            cur.execute("GRANT ALL ON SCHEMA public TO utsavai_app;")
        print("Runtime role utsavai_app configured successfully.")


if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATABASE_ADMIN_URL")
    if not db_url:
        print("Usage: python apply_supabase_migrations.py <DATABASE_ADMIN_URL>")
        sys.exit(1)
    run_migrations(db_url)
