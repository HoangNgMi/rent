# -*- coding: utf-8 -*-
"""migrate.py — Áp db/schema.sql vào DB `rent` (idempotent, psql -f). Fail-fast nếu thiếu PGPASSWORD."""
import os
import sys
import glob
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pgconn  # noqa: E402


def main():
    try:
        pgconn._prep()
    except Exception as e:
        print(f"✘ MIGRATE FAIL: không nạp được cấu hình (_VAULT/libpq): {str(e)[:200]}")
        return 1
    os.environ["PGCLIENTENCODING"] = "UTF8"
    os.environ.setdefault("PGCONNECT_TIMEOUT", "5")
    os.environ.setdefault("PGDATABASE", "rent")
    if not os.environ.get("PGPASSWORD"):
        print("✘ MIGRATE FAIL: chưa có khoá PostgreSQL trong _VAULT/rent.env (thiếu PGPASSWORD).")
        print("  → Cần: tạo DB `rent` + thêm PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE vào _VAULT/rent.env.")
        return 1
    psql = next(iter(sorted(glob.glob(r"C:\Program Files\PostgreSQL\*\bin\psql.exe"), reverse=True)), None)
    if not psql:
        print("✘ Không tìm thấy psql.exe trong C:\\Program Files\\PostgreSQL\\*\\bin")
        return 1
    schema = HERE / "schema.sql"
    if not schema.exists():
        print(f"✘ MIGRATE FAIL: thiếu file schema → {schema}")
        return 1
    try:
        r = subprocess.run([psql, "-v", "ON_ERROR_STOP=1", "-f", str(schema)],
                           env=os.environ.copy(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"✘ MIGRATE FAIL: không chạy được psql ({psql}): {str(e)[:200]}")
        return 1
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print("✘ MIGRATE FAIL:\n" + (r.stderr or "").strip())
        return 1
    print(f"✓ MIGRATE OK → {schema.name} (rental-intelligence schema + views)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
