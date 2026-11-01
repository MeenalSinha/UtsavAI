#!/usr/bin/env bash
# Lightweight repository secret/hardcode scan used locally and in CI.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
status=0
flag() { echo "FOUND: $1"; status=1; }

FILES=$(git ls-files 2>/dev/null || find . -type f -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/.next/*' -not -path '*/.git/*' -not -name 'package-lock.json' -not -name 'uv.lock')
FILES=$(echo "$FILES" | grep -v -E '(package-lock\.json|uv\.lock|openapi\.json|scan_secrets\.sh|\.png$|\.ico$)')

echo "$FILES" | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' && flag "committed .env file"
echo "$FILES" | xargs grep -n -E 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.' 2>/dev/null && flag "JWT-like token"
echo "$FILES" | xargs grep -n -E 'sb_secret_|service_role[\"'"'"']?\s*[:=]\s*[\"'"'"']ey' 2>/dev/null && flag "Supabase secret key"
echo "$FILES" | xargs grep -n -E 'AIza[0-9A-Za-z_-]{30,}' 2>/dev/null && flag "Google API key"
echo "$FILES" | xargs grep -n -E 'postgres(ql)?://[^:@/ ]+:[^@ ]{6,}@' 2>/dev/null \
  | grep -v -E 'CHANGE_ME|LOCAL_ONLY|ci_only|ci_runtime|placeholder|utsavai_local_only|example|<password>|<local-password>|pgadmin_local|:x@|YOUR-' && flag "database URL with password"
[ $status -eq 0 ] && echo "secret scan: clean"
exit $status
