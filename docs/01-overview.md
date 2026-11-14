# 01 — Tổng quan kiến trúc RENT (VeriMap Rental OS)

## Triết lý
Map-First (bản đồ là giao diện chính), lấy format Airbnb. Nền tảng **bán dữ liệu + quảng cáo + routing lead**, không môi giới trực tiếp. Vũ khí: **lọc tin ảo/giá mồi** + **lớp dữ liệu độc quyền** (ngập/ồn/expat) mà rao vặt thường không có.

## Luồng dữ liệu (DB → Map)
```
sim/generate.py ─► fact_listing (gồm tin ẢO)  ─┐
dim_building / dim_poi / dim_hazard / b2b ─────┤
                                               ▼
                         vw_building_card (SSOT: lọc ảo, price band, anti-fake stats)
                                               ▼
                  export_map_data.py ─► ui/data.js ─► index.html (Leaflet)
```
UI **chỉ hiển thị** measure đã tính ở SQL View (giống Traceable Numbers) — không tự lọc/tính.

## 2 góc nhìn trên cùng 1 map (toggle)
- **Tenant View:** giá trị cho khách — dữ liệu thật, chỉ số sống, Verified Specialist, mở khóa tin pass gấp.
- **B2B Revenue View:** dòng tiền cho Founder — slot QC tòa nhà, lead chuyển giao, B2B Map Proposal (SaaS).

## Geo + tích hợp bds
bds có 8 subzone `TPHCM_METRO` nhưng **không toạ độ**. RENT sở hữu tầng geo (lat/lng/bbox theo subzone), reuse NGUYÊN mã subzone của bds → `JOIN rent.fact_listing.subzone_code = bds.fact_bds_signals.subzone_code` để phủ tín hiệu thị trường thật (nhóm YIELD = cho thuê) lên bản đồ.

## Mở rộng
- Thêm subzone/tòa: sửa `sim/vocab.py` + `dim_subzone` (bbox) → chạy lại generate + export.
- Segment cho thuê riêng (khác bds mua-bán): CANHO/STUDIO/NHA_NGUYEN_CAN/PHONG/SHOPHOUSE.
