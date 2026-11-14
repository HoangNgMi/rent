# -*- coding: utf-8 -*-
"""pgconn.py — 1 cổng kết nối PostgreSQL cho dự án RENT. psycopg thuần-Python + libpq của PG.
Kết nối từ _VAULT/rent.env. connect(dbname='bds') để đọc DB nguồn khác (tích hợp sau)."""
import os
import sys
import glob
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _prep():
    for b in sorted(glob.glob(r"C:\Program Files\PostgreSQL\*\bin"), reverse=True):
        try:
            os.add_dll_directory(b)
        except Exception:
            pass
        os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")
        break
    os.environ.setdefault("PSYCOPG_IMPL", "python")
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    try:
        import vault_loader
        vault_loader.load("rent")
    except Exception:
        pass


def params():
    _prep()
    return dict(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "postgres"),
        dbname=os.environ.get("PGDATABASE", "rent"),
    )


def connect(dbname=None):
    p = params()
    if dbname:
        p["dbname"] = dbname
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(row_factory=dict_row, **p)
