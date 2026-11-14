# -*- coding: utf-8 -*-
"""pull_bds_signals.py — #1 TÍCH HỢP bds: đọc fact_bds_signals của Social/bds (qua creds rent,
dbname='bds' — né bug vault bds), gộp theo subzone_code → bảng rent.subzone_market_signal.
Join key = subzone_code (rent cấp geo, bds cấp tín hiệu thật). YIELD = cho thuê, DISTRESS = cắt lỗ.

    python etl/pull_bds_signals.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "db"))
import pgconn  # noqa: E402


def main():
    try:
        r = pgconn.connect()           # rent
    except Exception as e:
        print(f"✘ không kết nối `rent`: {type(e).__name__}: {str(e)[:120]}")
        return 1
    try:
        b = pgconn.connect(dbname="bds")   # đọc bds qua creds rent
    except Exception as e:
        print(f"✘ không kết nối `bds` (dbname=bds): {type(e).__name__}: {str(e)[:120]}")
        r.close(); return 1

    subs = [x["subzone_code"] for x in r.execute("SELECT subzone_code FROM dim_subzone").fetchall()]
    try:
        rows = b.execute(
            """SELECT f.subzone_code,
                      count(*)                                      AS total,
                      count(*) FILTER (WHERE f.signal_code='YIELD')    AS yld,
                      count(*) FILTER (WHERE f.signal_code='DISTRESS') AS dis,
                      count(*) FILTER (WHERE f.signal_code='CATALYST') AS cat,
                      COALESCE(sum(ds.health_direction), 0)         AS net
                 FROM fact_bds_signals f
                 LEFT JOIN dim_market_signals ds ON ds.signal_code = f.signal_code
                WHERE f.subzone_code = ANY(%s)
                GROUP BY f.subzone_code""",
            (subs,)).fetchall()
    finally:
        b.close()

    r.execute("DELETE FROM subzone_market_signal")   # idempotent (tránh ON CONFLICT mờ ám)
    for x in rows:
        r.execute(
            """INSERT INTO subzone_market_signal (subzone_code, total_signals, yield_count, distress_count, catalyst_count, net_health, synced_at)
               VALUES (%s,%s,%s,%s,%s,%s, now())""",
            (x["subzone_code"], x["total"], x["yld"], x["dis"], x["cat"], x["net"]))
    r.commit()
    r.close()
    print(f"✓ pull bds → subzone_market_signal: {len(rows)} subzone có tín hiệu (YIELD=cho thuê, DISTRESS=cắt lỗ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
