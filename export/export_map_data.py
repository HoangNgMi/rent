# -*- coding: utf-8 -*-
"""export_map_data.py — đọc các SQL View → ui/data.js (window.RENT_DATA). UI chỉ hiển thị.
Gồm: thẻ tòa (anti-fake + price band) · Deal Score · tín hiệu bds theo subzone · segment · meta subzone."""
import sys
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "db"))
import pgconn  # noqa: E402

USD = 24500
def to_usd(v): return int(round((v or 0) / USD))


def main():
    try:
        conn = pgconn.connect()
    except Exception as e:
        print(f"✘ EXPORT FAIL: {type(e).__name__}: {str(e)[:150]}")
        return 1
    try:
        area = conn.execute("SELECT subzone_name, center_lat, center_lng FROM dim_subzone WHERE subzone_code='HCM_KHU_DONG'").fetchone()
        cards = conn.execute("""
            SELECT c.*, b2.slot_status, b2.monthly_fee_vnd, b2.leads_month, b2.is_exclusive,
                   sp.name sp_name, sp.langs sp_langs, sp.verified sp_verified, sp.rating sp_rating
            FROM vw_building_card c
            LEFT JOIN building_b2b b2 ON b2.building_id=c.building_id
            LEFT JOIN dim_specialist sp ON sp.specialist_id=b2.specialist_id
            WHERE c.real_median_vnd IS NOT NULL ORDER BY c.subzone_code, c.name""").fetchall()
        deals = {r["building_id"]: r for r in conn.execute("SELECT building_id, deal_score, cheaper_pct FROM vw_building_deal").fetchall()}
        signals = {r["subzone_code"]: r for r in conn.execute("SELECT * FROM subzone_market_signal").fetchall()}
        szmeta = {r["subzone_code"]: r for r in conn.execute("SELECT subzone_code, subzone_name, listing_count, real_count, median_rent_vnd FROM vw_subzone_heat WHERE listing_count>0").fetchall()}
        bld_segs = defaultdict(list)
        for sr in conn.execute("SELECT building_id, segment, count(*) c FROM fact_listing WHERE is_verified AND NOT is_bait GROUP BY building_id, segment").fetchall():
            bld_segs[sr["building_id"]].append((sr["segment"], sr["c"]))
        pois = conn.execute("SELECT poi_id, poi_type, name, lat, lng FROM dim_poi").fetchall()
        hz = conn.execute("SELECT kind, lat, lng, radius_m, label FROM dim_hazard").fetchall()
        crm = conn.execute("SELECT count(*) nc FROM customers").fetchone()["nc"]
    finally:
        conn.close()

    def mkt(code):
        s = signals.get(code)
        return {"total": s["total_signals"], "yield": s["yield_count"], "distress": s["distress_count"], "net": s["net_health"]} if s else None

    buildings = []
    for c in cards:
        med = c["real_median_vnd"]
        d = deals.get(c["building_id"], {})
        segs = sorted(bld_segs.get(c["building_id"], []), key=lambda x: -x[1])
        buildings.append({
            "id": "B" + str(c["building_id"]), "code": c["code"], "name": c["name"],
            "subzone_code": c["subzone_code"], "lat": c["lat"], "lng": c["lng"],
            "median_usd": to_usd(med), "price_low_usd": to_usd(c["real_low_vnd"]), "price_high_usd": to_usd(c["real_high_vnd"]),
            "median_vnd": med, "rating": float(c["rating"]), "reviews": c["review_count"], "verified_units": c["real_kept"],
            "deal_score": d.get("deal_score"), "cheaper_pct": d.get("cheaper_pct"),
            "segments": [s[0] for s in segs], "top_segment": segs[0][0] if segs else None,
            "market": mkt(c["subzone_code"]),
            "anti_fake": {"scanned": c["scanned"], "fake_removed": c["fake_removed"], "real_kept": c["real_kept"], "bait_threshold_vnd": int((med or 0) * 0.62)},
            "price_band": {"online_fake_vnd": c["online_fake_vnd"] or int((med or 0) * 0.5), "real_median_vnd": med, "real_high_vnd": c["real_high_vnd"]},
            "living": {"mgmt_fee_vnd": c["mgmt_fee_vnd"], "parking_car_vnd": c["parking_car_vnd"], "parking_bike_vnd": c["parking_bike_vnd"],
                       "flood_risk": c["flood_risk"], "sun": c["sun"], "expat_ratio": c["expat_ratio"]},
            "specialist": {"name": c["sp_name"], "langs": c["sp_langs"], "verified": c["sp_verified"], "rating": float(c["sp_rating"]) if c["sp_rating"] else None},
            "b2b": {"slot_status": c["slot_status"], "monthly_fee_vnd": c["monthly_fee_vnd"], "leads_month": c["leads_month"],
                    "exclusive_to": (c["sp_name"] + " (Partner)") if (c["is_exclusive"] and c["sp_name"]) else None},
        })

    data = {
        "area": {"name": area["subzone_name"], "center": [area["center_lat"], area["center_lng"]], "zoom": 13},
        "buildings": buildings,
        "pois": [{"id": "P" + str(p["poi_id"]), "type": p["poi_type"], "name": p["name"], "lat": p["lat"], "lng": p["lng"]} for p in pois],
        "overlays": {
            "flood": [{"lat": h["lat"], "lng": h["lng"], "radius": h["radius_m"], "level": h["label"]} for h in hz if h["kind"] == "flood"],
            "noise": [{"lat": h["lat"], "lng": h["lng"], "radius": h["radius_m"], "level": h["label"]} for h in hz if h["kind"] == "noise"],
        },
        "subzones": [{"code": k, "name": v["subzone_name"], "median_vnd": v["median_rent_vnd"],
                      "listing_count": v["listing_count"], "market": mkt(k)} for k, v in szmeta.items()],
        "crm_customers": crm,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    out = ROOT / "ui" / "data.js"
    out.write_text("window.RENT_DATA = " + json.dumps(data, ensure_ascii=False, default=str, indent=2) + ";\n", encoding="utf-8")
    print(f"✓ export -> {out}  ({len(buildings)} tòa · {len(pois)} POI · {len(data['subzones'])} subzone có signal · {crm} khách)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
