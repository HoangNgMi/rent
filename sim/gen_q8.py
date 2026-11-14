# -*- coding: utf-8 -*-
"""gen_q8.py — sinh 50 căn cho thuê GIẢ LẬP ở Quận 8 (cũ), TP.HCM → ui/q8_data.js.
Standalone: KHÔNG cần DB/vault (demo chạy ngay). Reproducible (seed cố định). Giá VNĐ/tháng thực tế Q8.
"""
import json
import random
from pathlib import Path

random.seed(8)  # Quận 8

AREA = {"name": "Quận 8 (cũ) · TP.HCM", "center": [10.7238, 106.6296], "zoom": 14, "note": "Dọc Kênh Đôi — Phạm Thế Hiển"}
# bbox Q8 (đất liền, tránh rơi xuống kênh): lat 10.708–10.740 · lng 106.616–106.658
LAT = (10.7085, 10.7395)
LNG = (106.6165, 106.6575)

WARDS = ["P.4", "P.5", "P.6", "P.7", "P.8", "P.9", "P.11", "P.14", "P.15", "P.16",
         "Rạch Ông", "Xóm Củi", "Chánh Hưng", "Bình Đông", "Hưng Phú"]
STREETS = ["Phạm Thế Hiển", "Tùng Thiện Vương", "Dương Bá Trạc", "Cao Lỗ", "Bông Sao",
           "Âu Dương Lân", "Nguyễn Duy", "Tạ Quang Bửu", "Bến Bình Đông", "Lê Quang Kim",
           "An Dương Vương", "Trịnh Quang Nghị", "Hưng Phú", "Nguyễn Thị Tần", "Ba Đình",
           "Mễ Cốc", "Rạch Cát", "Liên Tỉnh 5", "Bình Đông", "Nguyễn Chế Nghĩa"]
# dự án căn hộ thật/giống thật ở Q8 & lân cận
PROJECTS = ["Diamond Lotus Riverside", "Topaz Elite", "Diamond Riverside", "Giai Việt",
            "The Avila", "Heaven Riverview", "Felisa Riverside", "Asa Light", "Soho Riverview",
            "Dream Home Riverside", "Tara Residence", "Pega Suite", "City Gate Towers",
            "Lucky Palace", "Conic Riverside", "Carillon"]

# segment: (code, nhãn, [rent_lo, rent_hi] triệu, [bed_lo, bed_hi], [m2_lo, m2_hi], trọng số)
SEGMENTS = [
    ("PHONG",      "Phòng DV / trọ",   2.8,  5.5, 1, 1, 18, 32, 24),
    ("STUDIO",     "Studio / Officetel", 5.0, 8.5, 0, 1, 28, 45, 18),
    ("CANHO_1PN",  "Căn hộ 1PN",        6.0, 9.5, 1, 1, 45, 58, 18),
    ("CANHO_2PN",  "Căn hộ 2PN",        8.5, 13.5, 2, 2, 60, 82, 20),
    ("CANHO_3PN",  "Căn hộ 3PN",       12.0, 20.0, 3, 3, 85, 115, 8),
    ("NHA_NC",     "Nhà nguyên căn",   10.0, 26.0, 2, 4, 60, 150, 8),
    ("SHOPHOUSE",  "Shophouse / MT",   18.0, 46.0, 0, 3, 80, 200, 4),
]
FURN = ["Đầy đủ nội thất", "Nội thất cơ bản", "Nhà trống"]
NOTES = ["view Kênh Đôi", "gần chợ Xóm Củi", "sát Phạm Thế Hiển", "gần cầu Chữ Y", "ban công thoáng",
         "có chỗ để ô tô", "gần trường tiểu học", "an ninh 24/7", "mới sơn sửa", "gần bến Bình Đông",
         "thang máy", "hẻm xe hơi", "gần Quận 5", "giờ giấc tự do", "wifi + máy giặt"]

def pick(lst):
    return random.choice(lst)

def wtpick(items, wkey):
    tot = sum(wkey(i) for i in items)
    r = random.uniform(0, tot)
    for i in items:
        r -= wkey(i)
        if r <= 0:
            return i
    return items[-1]

def round_vnd(trieu):
    """triệu(float) -> VNĐ làm tròn đẹp (bội 100k)."""
    return int(round(trieu * 1_000_000 / 100_000) * 100_000)

def gen():
    units = []
    used_codes = set()
    for i in range(1, 51):
        seg = wtpick(SEGMENTS, lambda s: s[8])
        code, label, rlo, rhi, blo, bhi, mlo, mhi, _ = seg
        # giá lệch về phía thấp (lognormal-ish) cho thực tế
        t = rlo + (rhi - rlo) * (random.random() ** 1.35)
        rent = round_vnd(t)
        beds = random.randint(blo, bhi)
        area = random.randint(mlo, mhi)
        ward = pick(WARDS)
        street = pick(STREETS)
        is_apt = code.startswith("CANHO") or code in ("STUDIO",)
        if is_apt:
            proj = pick(PROJECTS)
            name = f"{proj} · {beds or 'Studio'}" + ("PN" if beds else "")
        elif code == "PHONG":
            name = f"Phòng DV {street}"
        elif code == "NHA_NC":
            name = f"Nhà nguyên căn {street}"
        else:
            name = f"Shophouse {street}"
        # mã QB-#### (Q8)
        c = f"Q8-{random.randint(1000, 9999)}"
        while c in used_codes:
            c = f"Q8-{random.randint(1000, 9999)}"
        used_codes.add(c)
        lat = round(random.uniform(*LAT), 5)
        lng = round(random.uniform(*LNG), 5)
        months_dep = 2 if rent >= 8_000_000 else 1
        units.append({
            "id": f"q8_{i:02d}",
            "code": c,
            "name": name,
            "ward": ward,
            "street": street,
            "lat": lat, "lng": lng,
            "segment": code, "seg_label": label,
            "beds": beds, "area_m2": area,
            "rent_vnd": rent,
            "deposit_vnd": rent * months_dep,
            "rating": round(random.uniform(3.8, 4.9), 1),
            "reviews": random.randint(3, 58),
            "verified": random.random() < 0.72,
            "furnished": pick(FURN),
            "floor": (random.randint(2, 24) if is_apt else None),
            "note": pick(NOTES),
        })
    return units

def main():
    units = gen()
    out = {"area": AREA, "generated": "2026-11-14", "count": len(units), "units": units}
    dst = Path(__file__).resolve().parents[1] / "ui" / "q8_data.js"
    dst.write_text("window.Q8_DATA = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n",
                   encoding="utf-8")
    # thống kê nhanh
    segs = {}
    for u in units:
        segs[u["seg_label"]] = segs.get(u["seg_label"], 0) + 1
    rents = sorted(u["rent_vnd"] for u in units)
    print(f"✓ Ghi {len(units)} căn Q8 -> {dst}")
    print("  segment:", segs)
    print(f"  giá VNĐ/tháng: min {rents[0]/1e6:.1f}tr · trung vị {rents[len(rents)//2]/1e6:.1f}tr · max {rents[-1]/1e6:.1f}tr")

if __name__ == "__main__":
    main()
