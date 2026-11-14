# RENT — VeriMap Rental OS 🗺️

**Stack:** PostgreSQL · psycopg3 · SQL Views (deal/anti-fake/market) · Python (generator · ETL) · Leaflet + CartoDB · static-first (demo 0-backend) · zero-leakage shield

Nền tảng **Bản đồ Tình báo Thuê nhà & Dữ liệu B2B2C** (HCMC). Lấy cảm hứng giao diện Airbnb nhưng **Map-First**. Định vị: "Đơn vị Cung cấp Dữ liệu & Quảng cáo Công nghệ" (SaaS / Lead Routing), đứng trên vai đội Sales — KHÔNG môi giới trực tiếp.

## 2 phần
### (A) Prototype bản đồ — chạy NGAY, không cần DB
`ui/index.html` + `ui/app.js` + `ui/styles.css` + `ui/data.js` (Leaflet + CartoDB + Tailwind CDN).
- **Map-first 70% + drawer tình báo 30%.** Ghim nhà đen kiểu Airbnb · vòng bán kính đi bộ 800m · layer tiện ích · lớp phủ ngập/ồn.
- **Toggle đắt giá nhất:** `👁️ Tenant View` ↔ `💰 B2B Revenue View` — cùng 1 map, 2 góc nhìn (khách thấy giá trị / Chủ thấy tiền chảy).
- **3 khối drawer:** Anti-Fake Data Filter · Chỉ số Sống Thực tế · Trạm Kết nối/Ra tiền (đổi theo toggle).
- **Mở:** double-click `ui/index.html`.

### (B) Dataset "chuẩn Alex" — PostgreSQL + generator
`db/` (pgconn/migrate/schema) + `sim/` (vocab/generate) + `export/export_map_data.py`.
- Schema SSOT, mọi công thức ở **SQL View** (`vw_building_card`, `vw_subzone_heat`, GREATEST chống chia-0).
- **Tầng GEO** mà bds thiếu: `dim_subzone` (reuse 8 mã `TPHCM_METRO` của bds + toạ độ/bbox) · `dim_building` · `fact_listing` (lat/lng, có cả tin ẢO/MỒI để lọc) · `dim_poi` · `dim_specialist` · `building_b2b` · `dim_hazard`.
- Generator reproducible, sinh tòa + tin cho thuê realistic trong bbox từng subzone.

```
# sau khi có _VAULT/rent.env + DB rent:
python db/migrate.py
python sim/generate.py --buildings 42 --fresh
python export/export_map_data.py        # -> ui/data.js (thay mock bằng data thật)
# mở ui/index.html
```

## Nối hệ thống (sau)
- **Social/bds:** join key = `subzone_code` (rent cấp toạ độ, bds cấp **tín hiệu thật** — đặc biệt nhóm `YIELD` = cho thuê) → overlay nhiệt thị trường lên map.
- **ANALYTICS:** thêm `{project:"rent", db:"rent"}` vào `etl/sources.json` để chảy vào Medallion.

> Leaflet là "lệch có lý do" so với approved-stack (fit khung HTML tĩnh self-contained, tile OSM free).
