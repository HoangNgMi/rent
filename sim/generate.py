# -*- coding: utf-8 -*-
"""sim/generate.py — Generator giả lập CHUYÊN NGHIỆP cho RENT (tòa nhà + tin cho thuê HCMC).
Reproducible (seed) · scale (--buildings / --listings-per) · ghi thẳng DB qua psycopg.
Đọc geo subzone từ DB (dim_subzone), sinh toạ độ trong bbox từng subzone.

    python db/migrate.py
    python sim/generate.py --buildings 42 --fresh
"""
import sys
import random
import argparse
import hashlib
import collections
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "db")); sys.path.insert(0, str(ROOT))
import pgconn      # noqa: E402
import vocab as V  # noqa: E402


def wchoice(d):
    items = list(d.items()) if isinstance(d, dict) else list(d)
    vals, ws = zip(*items)
    return random.choices(vals, weights=ws, k=1)[0]


def jc(lo, hi):
    return round(random.uniform(lo, hi), 6)


def ensure_specialists(conn):
    if conn.execute("SELECT count(*) n FROM dim_specialist").fetchone()["n"] == 0:
        for name, langs in V.SPECIALISTS:
            conn.execute("INSERT INTO dim_specialist (name,langs,verified,rating) VALUES (%s,%s,TRUE,%s)",
                         (name, langs, round(random.uniform(4.6, 4.98), 2)))
        conn.commit()
    return [r["specialist_id"] for r in conn.execute("SELECT specialist_id FROM dim_specialist ORDER BY specialist_id").fetchall()]


def gen_crm(conn, spec_ids, n_cust):
    """#4 CRM: khách hàng PSEUDONYM (KH_<hash>) + touchpoint event-log Zalo. KHÔNG lưu raw PII."""
    blds = conn.execute("SELECT building_id, subzone_code FROM dim_building").fetchall()
    by_sub = collections.defaultdict(list)
    for b in blds:
        by_sub[b["subzone_code"]].append(b["building_id"])
    subs = list(by_sub.keys())
    seg_by_code = {s[0]: s for s in V.SEGMENTS}
    n_c = n_tp = 0
    for _ in range(n_cust):
        fake = f"0{random.randint(300000000, 999999999)}|{random.choice(V.HO)} {random.choice(V.TEN)}"
        mk = "KH_" + hashlib.sha256(fake.encode("utf-8")).hexdigest()[:8]
        sub = random.choice(subs)
        mix = V.SEGMENT_MIX.get(sub, V.SEGMENT_MIX["_default"])
        segc = wchoice([(s, mix.get(s, 1)) for s in seg_by_code])
        seg = seg_by_code[segc]
        stage = wchoice(V.STAGES)
        spec = random.choice(spec_ids)
        first = datetime.now(timezone.utc) - timedelta(days=int(random.random() * 120), hours=random.randint(0, 23))
        conn.execute(
            """INSERT INTO customers (ma_khach, subzone_interest, segment_interest, budget_min_vnd, budget_max_vnd,
                   nguon_lead, stage, assigned_specialist, first_seen)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (ma_khach) DO NOTHING""",
            (mk, sub, segc, int(seg[2] * 0.9 * 1e6), int(seg[3] * 1.1 * 1e6),
             wchoice(V.LEAD_SOURCES), stage, spec, first))
        n_c += 1
        t = first
        for _k in range(max(1, int(random.gauss(V.STAGE_DEPTH[stage], 1)))):
            t = t + timedelta(days=random.randint(1, 7), hours=random.randint(0, 12))
            bld = random.choice(by_sub[sub]) if by_sub.get(sub) else None
            conn.execute(
                """INSERT INTO touchpoints (ma_khach, specialist_id, building_id, channel, occurred_at, interaction, note, sentiment)
                   VALUES (%s,%s,%s,'Zalo',%s,%s,%s,%s)""",
                (mk, spec, bld, t, random.choice(V.INTERACTIONS), random.choice(V.TP_NOTES), random.choice([1, 1, 0, -1])))
            n_tp += 1
    conn.commit()
    return n_c, n_tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--buildings", type=int, default=42)
    ap.add_argument("--listings-per", type=int, default=28)
    ap.add_argument("--customers", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    random.seed(a.seed)

    try:
        conn = pgconn.connect()
    except Exception as e:
        print(f"✘ Không kết nối DB rent -> {type(e).__name__}: {str(e)[:150]}")
        return 1
    try:
        if a.fresh:
            conn.execute("TRUNCATE fact_listing, building_b2b, dim_building, dim_poi, dim_hazard, dim_specialist, customers, touchpoints, subzone_market_signal RESTART IDENTITY CASCADE")
            conn.commit()
            print("--fresh: đã xoá data cũ (giữ dim_subzone)")

        subs = {r["subzone_code"]: r for r in conn.execute("SELECT * FROM dim_subzone").fetchall()}
        if not subs:
            print("✘ Chưa có dim_subzone — chạy `python db/migrate.py` trước.")
            return 1
        spec_ids = ensure_specialists(conn)

        total_w = sum(V.SUBZONE_BUILDINGS.get(s, 1) for s in subs)
        counts = {s: max(1, round(a.buildings * V.SUBZONE_BUILDINGS.get(s, 1) / total_w)) for s in subs}
        seq = {}
        n_bld = n_lst = n_poi = 0

        for scode, sub in subs.items():
            names = list(V.BUILDING_NAMES.get(scode, []))
            random.shuffle(names)
            grade = sub["expat_grade"] or 1
            gmult = 0.5 + grade * 0.22
            pfx = scode.split("_")[-1][:3].upper()
            for i in range(counts[scode]):
                seq[pfx] = seq.get(pfx, 0) + 1
                bname = names[i] if i < len(names) else f"{sub['subzone_name'].split('—')[0].strip()} Residence {i + 1}"
                code = f"{pfx}-{seq[pfx]:03d}"
                lat, lng = jc(sub["lat_min"], sub["lat_max"]), jc(sub["lng_min"], sub["lng_max"])
                expat = min(95, max(5, int(grade * 14 + random.randint(-8, 12))))
                bid = conn.execute(
                    """INSERT INTO dim_building (code,name,subzone_code,lat,lng,rating,review_count,
                        mgmt_fee_vnd,parking_car_vnd,parking_bike_vnd,flood_risk,sun,expat_ratio)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING building_id""",
                    (code, bname, scode, lat, lng, round(random.uniform(4.5, 4.95), 2), random.randint(12, 60),
                     random.choice([14000, 15000, 16000, 18000, 20000, 22000, 24000]),
                     random.choice([1400000, 1500000, 1800000, 2000000, 2500000]),
                     random.choice([140000, 150000, 160000, 180000, 200000]),
                     random.choice(V.FLOOD), random.choice(V.SUN), expat)).fetchone()["building_id"]
                exclusive = random.random() < 0.65
                conn.execute(
                    "INSERT INTO building_b2b (building_id,specialist_id,slot_status,monthly_fee_vnd,leads_month,is_exclusive) VALUES (%s,%s,%s,%s,%s,%s)",
                    (bid, random.choice(spec_ids),
                     "Đang cho thuê độc quyền" if exclusive else "CÒN TRỐNG — chào thuê",
                     int(round(random.uniform(1.2, 3.0) * gmult, 1) * 1e6), random.randint(8, 34), exclusive))
                n_bld += 1

                mix = V.SEGMENT_MIX.get(scode, V.SEGMENT_MIX["_default"])
                for _ in range(max(6, int(random.gauss(a.listings_per, 6)))):
                    sc = wchoice(mix)
                    _, _, plo, phi, blo, bhi, alo, ahi = next(s for s in V.SEGMENTS if s[0] == sc)
                    price = int(round(random.uniform(plo, phi) * gmult * 1e6, -5))
                    bait = random.random() < 0.42
                    if bait:
                        price = int(price * random.uniform(0.35, 0.6))
                    verified = (not bait) and random.random() < 0.55
                    listed = datetime.now(timezone.utc) - timedelta(days=int(random.random() ** 0.7 * 180), hours=random.randint(0, 23))
                    beds = random.randint(blo, bhi)
                    conn.execute(
                        """INSERT INTO fact_listing (building_id,subzone_code,segment,price_vnd,area_m2,bedrooms,bathrooms,
                            status,is_verified,is_bait,source,listed_at,lat,lng)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (bid, scode, sc, price, random.randint(alo, ahi), beds, max(1, beds),
                         wchoice(V.STATUS_WEIGHTS), verified, bait, wchoice(V.SOURCES), listed,
                         round(lat + random.uniform(-0.0012, 0.0012), 6), round(lng + random.uniform(-0.0012, 0.0012), 6)))
                    n_lst += 1
            conn.commit()

            if grade >= 3:
                for ptype, cnt in V.POI_PER_SUBZONE.items():
                    pool = list(V.POI_TEMPLATES[ptype]); random.shuffle(pool)
                    tag = sub["subzone_name"].split("—")[0].strip().split("/")[0].strip()
                    for j in range(cnt):
                        conn.execute("INSERT INTO dim_poi (poi_type,name,subzone_code,lat,lng) VALUES (%s,%s,%s,%s,%s)",
                                     (ptype, f"{pool[j % len(pool)]} · {tag}", scode,
                                      jc(sub["lat_min"], sub["lat_max"]), jc(sub["lng_min"], sub["lng_max"])))
                        n_poi += 1
                for _k in range(2):
                    conn.execute("INSERT INTO dim_hazard (subzone_code,kind,lat,lng,radius_m,label) VALUES (%s,'flood',%s,%s,%s,%s)",
                                 (scode, jc(sub["lat_min"], sub["lat_max"]), jc(sub["lng_min"], sub["lng_max"]), random.choice([280, 320, 350]), "Cảnh báo ngập khi mưa lớn"))
                conn.execute("INSERT INTO dim_hazard (subzone_code,kind,lat,lng,radius_m,label) VALUES (%s,'noise',%s,%s,%s,%s)",
                             (scode, jc(sub["lat_min"], sub["lat_max"]), jc(sub["lng_min"], sub["lng_max"]), random.choice([260, 300]), "Ồn — gần trục giao thông lớn"))
                conn.commit()

        nc, ntp = gen_crm(conn, spec_ids, a.customers)
        print(f"\n✓ XONG. {n_bld} tòa · {n_lst} tin cho thuê · {n_poi} POI · {nc} khách (KH_) · {ntp} touchpoint")
        for r in conn.execute("""SELECT s.subzone_name nm, count(DISTINCT b.building_id) toa, count(l.listing_id) tin,
                                        round(count(*) FILTER (WHERE l.is_bait)*100.0/GREATEST(count(l.listing_id),1),0) fake
                                   FROM dim_subzone s LEFT JOIN dim_building b ON b.subzone_code=s.subzone_code
                                   LEFT JOIN fact_listing l ON l.building_id=b.building_id
                                   GROUP BY s.subzone_name HAVING count(l.listing_id)>0 ORDER BY tin DESC""").fetchall():
            print(f"   {r['nm'][:40]:42s} {r['toa']:3d} tòa · {r['tin']:5d} tin · ảo {r['fake']}%")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
