"""Lightweight repository secret/hardcode scan."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
files_out = subprocess.check_output(["git", "ls-files"], cwd=root, text=True)
files = [
    f
    for f in files_out.splitlines()
    if not any(
        x in f
        for x in [
            "package-lock.json",
            "uv.lock",
            "openapi.json",
            "scan_secrets",
            ".png",
            ".ico",
        ]
    )
]

flags: list[tuple[str, str, int]] = []
for rel in files:
    p = root / rel
    if rel.endswith(".env") or (".env." in rel and not rel.endswith(".env.example")):
        flags.append(("committed .env file", rel, 0))
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for idx, line in enumerate(content.splitlines(), start=1):
        if re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.", line):
            flags.append(("JWT-like token", rel, idx))
        if re.search(r"sb_secret_|service_role[\"']?\s*[:=]\s*[\"']ey", line):
            flags.append(("Supabase secret key", rel, idx))
        if re.search(r"AIza[0-9A-Za-z_-]{30,}", line):
            flags.append(("Google API key", rel, idx))
        m = re.search(r"postgres(ql)?://[^:@/ ]+:[^@ ]{6,}@", line)
        if m:
            ignored = [
                "CHANGE_ME",
                "LOCAL_ONLY",
                "ci_only",
                "ci_runtime",
                "placeholder",
                "utsavai_local_only",
                "example",
                "<password>",
                "<local-password>",
                "pgadmin_local",
                ":x@",
                "YOUR-",
            ]
            if not any(ig in line for ig in ignored):
                flags.append(("Database URL with password", rel, idx))

if flags:
    for f in flags:
        print(f"FOUND: {f[0]} in {f[1]}:{f[2]}")
    sys.exit(1)

print("Secret scan: CLEAN")
