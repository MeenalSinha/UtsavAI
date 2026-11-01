#!/usr/bin/env bash
# Creates a throwaway LOCAL PostgreSQL database, applies the Supabase stand-ins
# plus every migration, and enables LOGIN for the runtime role.
#
# Usage: ADMIN_URL=postgresql://postgres@localhost:5432/postgres scripts/setup_local_db.sh [dbname]
# Never point this at a Supabase project: it drops and recreates the database.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADMIN_URL="${ADMIN_URL:?Set ADMIN_URL to a superuser connection URL for a LOCAL postgres server}"
DB_NAME="${1:-utsavai_test}"
APP_PASSWORD="${APP_ROLE_PASSWORD:-utsavai_local_only}"

case "$ADMIN_URL" in
  *supabase.co*|*supabase.com*|*pooler.supabase*)
    echo "Refusing to run against a Supabase host." >&2; exit 1 ;;
esac

BASE="${ADMIN_URL%/*}"
psql "$ADMIN_URL" -v ON_ERROR_STOP=1 -q -c "drop database if exists \"$DB_NAME\" with (force)" -c "create database \"$DB_NAME\""
TARGET="$BASE/$DB_NAME"

psql "$TARGET" -v ON_ERROR_STOP=1 -q -f "$ROOT/supabase/tests/bootstrap_local.sql"
for f in "$ROOT"/supabase/migrations/*.sql; do
  echo "applying $(basename "$f")"
  psql "$TARGET" -v ON_ERROR_STOP=1 -q -f "$f"
done
psql "$TARGET" -v ON_ERROR_STOP=1 -q -c "alter role utsavai_app login password '$APP_PASSWORD'"
echo "Database ready: $TARGET"
echo "Runtime URL: ${BASE/\/\/*@/\/\/utsavai_app:$APP_PASSWORD@}/$DB_NAME"
