# -*- coding: utf-8 -*-
"""sim/vocab.py — chất liệu miền CHO THUÊ TP.HCM cho generator. Sửa ở đây để đổi giọng data."""

# số tòa sinh mỗi subzone (trọng số) — dồn vào các hub cho thuê thật
SUBZONE_BUILDINGS = {
    "HCM_KHU_DONG": 14, "HCM_KHU_NAM": 12, "HCM_TRUNG_TAM_TAY": 8,
    "BD_THUAN_DI_AN": 3, "DNAI_NHON_TRACH_LT": 2, "BRVT_HO_TRAM_PHU_MY": 2,
    "HCM_CAN_GIO": 1, "LA_DUC_HOA_BEN_LUC": 1,
}

# tên tòa thật/giống thật theo subzone (xoay vòng + số)
BUILDING_NAMES = {
    "HCM_KHU_DONG": ["Masteri Thảo Điền", "The Nassim", "Gateway Thảo Điền", "Estella Heights",
                     "The Vista An Phú", "d'Edge Thảo Điền", "Feliz en Vista", "Q2 Thảo Điền",
                     "Masteri An Phú", "The River Thủ Thiêm", "Thảo Điền Pearl", "Empire City",
                     "Metropole Thủ Thiêm", "Sala Sarimi"],
    "HCM_KHU_NAM": ["The Panorama", "Riverpark Premier", "Sky Garden", "Happy Valley", "Midtown Phú Mỹ Hưng",
                    "Scenic Valley", "Nam Phúc Le Jardin", "Grand View", "Cảnh Viên", "Hưng Vượng",
                    "The Signature", "Urban Hill"],
    "HCM_TRUNG_TAM_TAY": ["Saigon Royal", "Vinhomes Golden River", "The Grand Manhattan", "The Marq",
                          "Madison Q1", "Léman Luxury", "City Garden", "Serenity Sky Villas"],
    "BD_THUAN_DI_AN": ["Astral City", "The Emerald Golf View", "Charm City"],
    "DNAI_NHON_TRACH_LT": ["Swan Bay", "Aqua City"],
    "BRVT_HO_TRAM_PHU_MY": ["Ixora Hồ Tràm", "The Hamptons"],
    "HCM_CAN_GIO": ["Cần Giờ Riverside"],
    "LA_DUC_HOA_BEN_LUC": ["Waterpoint Bến Lức"],
}

# segment cho thuê: (code, nhãn, [giá lo, hi] triệu/tháng, [bed lo, hi], [m2 lo, hi])
SEGMENTS = [
    ("CANHO",          "Căn hộ",        12, 38, 1, 3, 45, 120),
    ("STUDIO",         "Studio/Officetel", 8, 16, 0, 1, 28, 45),
    ("NHA_NGUYEN_CAN", "Nhà nguyên căn", 25, 80, 2, 5, 80, 250),
    ("PHONG",          "Phòng DV/trọ",   3.5, 9, 1, 1, 18, 35),
    ("SHOPHOUSE",      "Shophouse",      30, 110, 0, 2, 60, 200),
]
# mix segment theo subzone (code segment -> trọng số)
SEGMENT_MIX = {
    "HCM_KHU_DONG": {"CANHO": 55, "STUDIO": 20, "NHA_NGUYEN_CAN": 12, "PHONG": 8, "SHOPHOUSE": 5},
    "HCM_KHU_NAM": {"CANHO": 60, "STUDIO": 15, "NHA_NGUYEN_CAN": 15, "PHONG": 5, "SHOPHOUSE": 5},
    "HCM_TRUNG_TAM_TAY": {"CANHO": 40, "STUDIO": 35, "PHONG": 15, "SHOPHOUSE": 10},
    "_default": {"CANHO": 45, "STUDIO": 15, "NHA_NGUYEN_CAN": 25, "PHONG": 10, "SHOPHOUSE": 5},
}

STATUS_WEIGHTS = [("trong", 62), ("da_thue", 30), ("giu_cho", 8)]
SOURCES = [("direct", 40), ("sales_partner", 35), ("scrape", 25)]
SUN = ["Đông Nam", "Nam", "Đông", "Tây Nam", "Bắc"]
FLOOD = ["Rất thấp", "Thấp", "Thấp", "Trung bình", "Cao"]

SPECIALISTS = [
    ("David Nguyễn", "EN · VI"), ("Emma Trần", "EN · VI · KR"), ("Michael Lê", "EN · VI"),
    ("Sophie Phạm", "EN · VI · FR"), ("Lan Hoàng", "EN · VI"), ("Kevin Vũ", "EN · VI · JP"),
    ("Anna Đỗ", "EN · VI"), ("Henry Bùi", "EN · VI · ZH"), ("Lily Ngô", "EN · VI"),
    ("Daniel Phan", "EN · VI"), ("Grace Lý", "EN · VI · KR"), ("Tom Đặng", "EN · VI"),
]

# POI templates theo type (tên + số lượng sinh mỗi subzone đô thị)
POI_TEMPLATES = {
    "dining": ["The Deck", "Boat House", "Soul Burger", "Annam Gourmet", "Pizza 4P's", "The Running Bean",
               "L'Usine", "Quán Bụi", "Nam An Market"],
    "park": ["Riverside Park", "Central Park", "Sala Park", "California Fitness", "Yoga Plus", "Crescent Walk"],
    "school": ["British Int'l School", "ISHCMC", "European Int'l School", "AIS Saigon", "Renaissance Int'l",
               "Western Academy"],
    "metro": ["Metro L1 Station", "Metro L1 Depot", "BRT Hub", "Bus Rapid Terminal"],
    "coworking": ["Dreamplex", "WeWork", "Toong", "CirCO"],
}
POI_PER_SUBZONE = {"dining": 4, "park": 2, "school": 3, "metro": 2, "coworking": 1}  # cho subzone đô thị (grade>=3)

# ---- #4 CRM ----
STAGES = [("lead", 35), ("quan_tam", 28), ("di_xem", 20), ("thuong_luong", 10), ("chot", 7)]
STAGE_DEPTH = {"lead": 1, "quan_tam": 2, "di_xem": 4, "thuong_luong": 6, "chot": 7}
LEAD_SOURCES = [("Zalo", 40), ("Facebook", 22), ("Giới thiệu", 20), ("Website", 12), ("CTV", 6)]
INTERACTIONS = ["nhắn Zalo hỏi phòng", "gọi điện tư vấn", "gửi ảnh/clip căn", "hẹn đi xem",
                "đi xem thực tế", "thương lượng giá", "gửi hợp đồng mẫu", "nhắc lịch", "follow-up sau xem"]
TP_NOTES = ["khách quan tâm view sông", "cần gần trường quốc tế", "ngân sách hơi thấp so với khu",
            "muốn vào ở đầu tháng", "so sánh 2-3 căn", "chốt nếu giảm chút", "khách Tây cần chuyên viên song ngữ",
            "hẹn cuối tuần đi xem", "đang cân nhắc khu khác", "ưng căn nhưng chờ công ty duyệt"]
# tên (chỉ để sinh pseudonym KH_<hash> — KHÔNG lưu raw vào DB)
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
TEN = ["An", "Bình", "Chi", "Dung", "Hà", "Hải", "Hạnh", "Hiếu", "Hoa", "Hùng", "Lan", "Linh", "Mai", "Minh",
       "Nam", "Nga", "Ngọc", "Phúc", "Quân", "Sơn", "Tâm", "Thảo", "Trang", "Tuấn", "Vy"]
