# Deploy prototype RENT lên Vercel (0đ, static)

Prototype là **HTML tĩnh self-contained** (`ui/index.html` + `app.js` + `styles.css` + `data.js` + CDN Leaflet/Tailwind). Deploy thư mục `ui/`:

## Cách 1 — Vercel CLI
```
npm i -g vercel        # 1 lần, nếu chưa có
cd ui
vercel --prod          # Vercel tự nhận static → trả link https://... ngay
```

## Cách 2 — Kéo-thả (không cần CLI)
Vào [vercel.com](https://vercel.com) → New Project → import repo (hoặc kéo-thả thư mục `ui/`) → Deploy.

## Cập nhật data sau này
`python export/export_map_data.py` ghi lại `ui/data.js` (data thật từ generator + tín hiệu bds) → deploy lại.

> Tile bản đồ dùng CartoDB/OSM (free). Không cần API key. Không lộ secret (prototype chỉ có data đã export, không chứa `_VAULT`).
