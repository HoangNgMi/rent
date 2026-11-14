-- ============================================================
--  RENT — VeriMap Rental OS (Bản đồ Tình báo Thuê nhà HCMC)
--  DB: rent (PG local). SSOT: mọi công thức ở SQL VIEW; UI chỉ đọc. Áp: python db/migrate.py
--  Reuse 8 subzone TPHCM_METRO của Social/bds + BỔ SUNG tầng GEO (bds thiếu toạ độ).
-- ============================================================

-- 🗺️ dim_subzone — tái dùng mã subzone của bds + thêm center/bbox để sinh toạ độ + join bds.subzone_code
CREATE TABLE IF NOT EXISTS dim_subzone (
    subzone_code  TEXT PRIMARY KEY,
    subzone_name  TEXT NOT NULL,
    center_lat    DOUBLE PRECISION, center_lng DOUBLE PRECISION,
    lat_min DOUBLE PRECISION, lat_max DOUBLE PRECISION, lng_min DOUBLE PRECISION, lng_max DOUBLE PRECISION,
    expat_grade   INT,          -- 1..5 (độ "Tây hoá" / cao cấp cho thuê)
    investment_dna TEXT
);
INSERT INTO dim_subzone (subzone_code, subzone_name, center_lat, center_lng, lat_min, lat_max, lng_min, lng_max, expat_grade, investment_dna) VALUES
  ('HCM_KHU_DONG','Khu Đông — Thảo Điền/An Phú/Thủ Đức', 10.8035,106.7378, 10.7955,10.8120, 106.7250,106.7560, 5,'Căn hộ cao cấp, cộng đồng expat đông, gần trường quốc tế'),
  ('HCM_KHU_NAM','Khu Nam — Phú Mỹ Hưng/Q7/Nhà Bè',     10.7290,106.7180, 10.7150,10.7450, 106.7000,106.7360, 5,'Đô thị kiểu mẫu, Hàn/Nhật/Đài đông, tiện ích đồng bộ'),
  ('HCM_TRUNG_TAM_TAY','Trung tâm–Tây — Q1/3/5/Bình Tân',10.7760,106.6950, 10.7600,10.7920, 106.6800,106.7100, 3,'Trung tâm, officetel/studio, khách công tác ngắn hạn'),
  ('HCM_CAN_GIO','Cần Giờ',                               10.4100,106.9550, 10.3800,10.4400, 106.9200,106.9900, 1,'Ven biển, nghỉ dưỡng, cho thuê thấp'),
  ('BD_THUAN_DI_AN','Dĩ An–Thuận An (QL13)',              10.9000,106.7700, 10.8700,10.9300, 106.7400,106.8000, 2,'Giáp ranh, công nhân/chuyên gia KCN'),
  ('BRVT_HO_TRAM_PHU_MY','Phú Mỹ–Hồ Tràm',                10.5800,107.0900, 10.5400,10.6200, 107.0500,107.1300, 2,'Ven biển nghỉ dưỡng, thuê ngắn hạn'),
  ('DNAI_NHON_TRACH_LT','Nhơn Trạch–Long Thành',          10.7500,106.9000, 10.7100,10.7900, 106.8600,106.9400, 1,'Vùng sân bay Long Thành, cho thuê chuyên gia'),
  ('LA_DUC_HOA_BEN_LUC','Đức Hòa–Bến Lức',                10.6500,106.4700, 10.6100,10.6900, 106.4300,106.5100, 1,'Giáp Tây HCM, thuê công nhân/kỹ sư')
ON CONFLICT (subzone_code) DO UPDATE SET
  subzone_name=excluded.subzone_name, center_lat=excluded.center_lat, center_lng=excluded.center_lng,
  lat_min=excluded.lat_min, lat_max=excluded.lat_max, lng_min=excluded.lng_min, lng_max=excluded.lng_max,
  expat_grade=excluded.expat_grade, investment_dna=excluded.investment_dna;

-- 🧑‍💼 chuyên viên (Verified Building Specialist)
CREATE TABLE IF NOT EXISTS dim_specialist (
    specialist_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL, langs TEXT, verified BOOLEAN DEFAULT TRUE, rating NUMERIC(3,2)
);

-- 🏢 tòa nhà (Primary Node trên map)
CREATE TABLE IF NOT EXISTS dim_building (
    building_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    subzone_code TEXT REFERENCES dim_subzone(subzone_code),
    lat DOUBLE PRECISION, lng DOUBLE PRECISION,
    rating NUMERIC(3,2), review_count INT,
    mgmt_fee_vnd BIGINT, parking_car_vnd BIGINT, parking_bike_vnd BIGINT,
    flood_risk TEXT, sun TEXT, expat_ratio INT
);
CREATE INDEX IF NOT EXISTS ix_building_subzone ON dim_building(subzone_code);

-- 💰 trạm B2B theo tòa (slot QC + chuyên viên độc quyền + lead)
CREATE TABLE IF NOT EXISTS building_b2b (
    building_id INT PRIMARY KEY REFERENCES dim_building(building_id),
    specialist_id INT REFERENCES dim_specialist(specialist_id),
    slot_status TEXT, monthly_fee_vnd BIGINT, leads_month INT, is_exclusive BOOLEAN DEFAULT FALSE
);

-- 📍 POI tiện ích
CREATE TABLE IF NOT EXISTS dim_poi (
    poi_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    poi_type TEXT NOT NULL,     -- dining|park|school|metro|coworking
    name TEXT NOT NULL, subzone_code TEXT REFERENCES dim_subzone(subzone_code),
    lat DOUBLE PRECISION, lng DOUBLE PRECISION
);

-- ⚠️ lớp phủ cảnh báo (vũ khí dữ liệu: ngập/ồn)
CREATE TABLE IF NOT EXISTS dim_hazard (
    hazard_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subzone_code TEXT, kind TEXT,  -- flood|noise
    lat DOUBLE PRECISION, lng DOUBLE PRECISION, radius_m INT, label TEXT
);

-- 🧾 fact_listing — grain = 1 tin cho thuê (gồm cả tin ẢO/MỒI để lọc)
CREATE TABLE IF NOT EXISTS fact_listing (
    listing_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    building_id INT REFERENCES dim_building(building_id),
    subzone_code TEXT REFERENCES dim_subzone(subzone_code),
    segment TEXT,              -- CANHO|STUDIO|NHA_NGUYEN_CAN|PHONG|SHOPHOUSE
    price_vnd BIGINT,          -- giá thuê / tháng
    area_m2 INT, bedrooms INT, bathrooms INT,
    status TEXT DEFAULT 'trong',  -- trong|da_thue|giu_cho
    is_verified BOOLEAN DEFAULT FALSE,  -- đã kiểm chứng hiện trường
    is_bait BOOLEAN DEFAULT FALSE,      -- tin ảo / giá mồi
    source TEXT, listed_at TIMESTAMPTZ DEFAULT now(),
    lat DOUBLE PRECISION, lng DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS ix_listing_building ON fact_listing(building_id);
CREATE INDEX IF NOT EXISTS ix_listing_subzone  ON fact_listing(subzone_code);

-- ============================================================
--  SQL VIEWS — SSOT công thức (UI/BI chỉ đọc; GREATEST chống chia-0)
-- ============================================================

-- Thẻ tòa nhà: thống kê Anti-Fake + price band + chỉ số sống (từ fact_listing)
CREATE OR REPLACE VIEW vw_building_card AS
SELECT b.building_id, b.code, b.name, b.subzone_code, b.lat, b.lng, b.rating, b.review_count,
       b.mgmt_fee_vnd, b.parking_car_vnd, b.parking_bike_vnd, b.flood_risk, b.sun, b.expat_ratio,
       count(l.listing_id)                                              AS scanned,
       count(*) FILTER (WHERE l.is_bait)                                AS fake_removed,
       count(*) FILTER (WHERE l.is_verified AND NOT l.is_bait AND l.status='trong') AS real_kept,
       min(l.price_vnd) FILTER (WHERE l.is_bait)                        AS online_fake_vnd,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY l.price_vnd)
         FILTER (WHERE l.is_verified AND NOT l.is_bait)                 AS real_median_vnd,
       max(l.price_vnd) FILTER (WHERE l.is_verified AND NOT l.is_bait)  AS real_high_vnd,
       min(l.price_vnd) FILTER (WHERE l.is_verified AND NOT l.is_bait)  AS real_low_vnd
FROM dim_building b
LEFT JOIN fact_listing l ON l.building_id = b.building_id
GROUP BY b.building_id;

-- Nhiệt thị trường theo subzone (join key tương lai với bds.fact_bds_signals.subzone_code)
CREATE OR REPLACE VIEW vw_subzone_heat AS
SELECT s.subzone_code, s.subzone_name, s.expat_grade,
       count(l.listing_id)                                              AS listing_count,
       count(*) FILTER (WHERE l.is_verified AND NOT l.is_bait)          AS real_count,
       round(100.0 * count(*) FILTER (WHERE l.is_bait) / GREATEST(count(l.listing_id),1), 1) AS fake_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY l.price_vnd)
         FILTER (WHERE l.is_verified AND NOT l.is_bait)                 AS median_rent_vnd
FROM dim_subzone s
LEFT JOIN fact_listing l ON l.subzone_code = s.subzone_code
GROUP BY s.subzone_code, s.subzone_name, s.expat_grade;

-- ============================================================
--  MỞ RỘNG — #1 tín hiệu bds · #3 Deal Score · #4 CRM
-- ============================================================
-- #1: tín hiệu thị trường bơm từ Social/bds (etl/pull_bds_signals.py, join subzone_code)
CREATE TABLE IF NOT EXISTS subzone_market_signal (
    subzone_code  TEXT PRIMARY KEY REFERENCES dim_subzone(subzone_code),
    total_signals INT DEFAULT 0, yield_count INT DEFAULT 0, distress_count INT DEFAULT 0,
    catalyst_count INT DEFAULT 0, net_health INT DEFAULT 0, synced_at TIMESTAMPTZ
);

-- #4: CRM — khách hàng PSEUDONYM (KH_), touchpoint event-log (ghi tay Zalo). KHÔNG raw PII.
CREATE TABLE IF NOT EXISTS customers (
    ma_khach         TEXT PRIMARY KEY,
    subzone_interest TEXT REFERENCES dim_subzone(subzone_code),
    segment_interest TEXT, budget_min_vnd BIGINT, budget_max_vnd BIGINT,
    nguon_lead TEXT, stage TEXT DEFAULT 'lead',
    assigned_specialist INT REFERENCES dim_specialist(specialist_id),
    first_seen TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS touchpoints (
    tp_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ma_khach TEXT REFERENCES customers(ma_khach),
    specialist_id INT REFERENCES dim_specialist(specialist_id),
    building_id INT REFERENCES dim_building(building_id),
    channel TEXT DEFAULT 'Zalo', occurred_at TIMESTAMPTZ, interaction TEXT, note TEXT, sentiment INT
);
CREATE INDEX IF NOT EXISTS ix_tp_khach ON touchpoints(ma_khach);

-- #3: median thuê theo subzone + Deal Score mỗi tòa (giá thật tòa vs median subzone)
CREATE OR REPLACE VIEW vw_subzone_median AS
SELECT s.subzone_code,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY l.price_vnd)
         FILTER (WHERE l.is_verified AND NOT l.is_bait) AS median_rent_vnd
FROM dim_subzone s LEFT JOIN fact_listing l ON l.subzone_code = s.subzone_code
GROUP BY s.subzone_code;

CREATE OR REPLACE VIEW vw_building_deal AS
SELECT c.building_id, c.subzone_code, c.real_median_vnd, m.median_rent_vnd AS subzone_median,
       round(100.0 * (m.median_rent_vnd - c.real_median_vnd) / GREATEST(m.median_rent_vnd, 1))::int AS cheaper_pct,
       -- Deal Score 0..100: 50 = bằng median khu; rẻ hơn → cao hơn (rẻ hơn 20% ≈ 70)
       LEAST(100, GREATEST(0, 50 + round((m.median_rent_vnd - c.real_median_vnd) * 100.0 / GREATEST(m.median_rent_vnd, 1))))::int AS deal_score
FROM vw_building_card c
LEFT JOIN vw_subzone_median m ON m.subzone_code = c.subzone_code
WHERE c.real_median_vnd IS NOT NULL;
