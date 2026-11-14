/* app.js — VeriMap Rental OS (prototype). Map-first + drawer tình báo + toggle Tenant/B2B. */
(function () {
  "use strict";
  const D = window.RENT_DATA;
  const AB = "#E61E4D";
  const HOUSE = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.6 12 3l9 7.6"/><path d="M5.5 9.4V20h13V9.4"/></svg>';
  const WALK_M = 800;
  const POI_LABEL = { dining: "🍽️ Dining", park: "🌳 Parks", school: "🏫 Schools", metro: "🚇 Transit", coworking: "💼 Cowork" };
  const POI_COLOR = { dining: "#f59e0b", park: "#22c55e", school: "#ec4899", metro: "#3b82f6", coworking: "#8b5cf6" };
  const SEG_LABEL = { CANHO: "Căn hộ", STUDIO: "Studio", NHA_NGUYEN_CAN: "Nhà NC", PHONG: "Phòng DV", SHOPHOUSE: "Shophouse" };

  const state = {
    view: "tenant",
    bldTab: "map",
    selected: null,
    layers: { dining: true, park: true, school: true, metro: true, coworking: true, flood: false },
    search: "",
    filters: { priceMax: 0, subzone: "", segment: "", dealOnly: false },
  };
  const bldMarkers = {}, poiMarkers = {}, overlayShapes = [];
  let walkCircle = null;

  // ---------- helpers ----------
  const vnd = (n) => (n == null ? "—" : (n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "tr" : Math.round(n / 1e3) + "k"));
  const usd = (n) => "$" + n;
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  function dist(a, b, c, d) { // haversine mét
    const R = 6371000, t = Math.PI / 180;
    const x = Math.sin((c - a) * t / 2) ** 2 + Math.cos(a * t) * Math.cos(c * t) * Math.sin((d - b) * t / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }

  // ---------- map ----------
  const map = L.map("map", { zoomControl: true, attributionControl: false }).setView(D.area.center, D.area.zoom);
  // Nền: Esri World Street Map (KHÔNG cần API key; CartoDB free đã đòi key). Dự phòng: OSM.de.
  const _esri = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Tiles © Esri" }).addTo(map);
  const _osmde = L.tileLayer("https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png", { subdomains: "abc", maxZoom: 19, attribution: "© OpenStreetMap" });
  let _fb = false;
  _esri.on("tileerror", () => { if (!_fb) { _fb = true; map.removeLayer(_esri); _osmde.addTo(map); } });
  // map có thể init trước khi layout ổn (Tailwind CDN trễ) -> ép tính lại kích thước
  const _fix = () => map.invalidateSize();
  setTimeout(_fix, 250); setTimeout(_fix, 700);
  window.addEventListener("load", _fix); window.addEventListener("resize", _fix);

  // POI markers
  D.pois.forEach((p) => {
    const m = L.marker([p.lat, p.lng], {
      icon: L.divIcon({ className: "poi-pin poi-" + p.type, html: '<div class="pdot"></div>', iconSize: [15, 15] }),
    }).addTo(map);
    m.bindTooltip(POI_LABEL[p.type].slice(2) + ": " + p.name, { direction: "top", offset: [0, -6] });
    poiMarkers[p.id] = { m, p };
  });

  // Building markers
  D.buildings.forEach((b) => {
    const m = L.marker([b.lat, b.lng], {
      icon: L.divIcon({ className: "bld-pin", html: '<div class="dot">' + HOUSE + '</div><div class="price">' + usd(b.median_usd) + "/mo</div>", iconSize: [34, 34], iconAnchor: [17, 17] }),
      zIndexOffset: 1000,
    }).addTo(map);
    m.on("click", () => selectBuilding(b.id));
    bldMarkers[b.id] = { m, b };
  });

  // ---------- selection + walkability ----------
  function selectBuilding(id) {
    state.selected = id;
    const b = bldMarkers[id].b;
    Object.values(bldMarkers).forEach((o) => o.m.getElement() && o.m.getElement().classList.toggle("selected", o.b.id === id));
    if (walkCircle) map.removeLayer(walkCircle);
    walkCircle = L.circle([b.lat, b.lng], { radius: WALK_M, color: AB, weight: 1.5, fillColor: AB, fillOpacity: 0.07 }).addTo(map);
    // sáng POI trong bán kính
    Object.values(poiMarkers).forEach((o) => {
      const near = dist(b.lat, b.lng, o.p.lat, o.p.lng) <= WALK_M && state.layers[o.p.type];
      const el = o.m.getElement(); if (el) el.classList.toggle("lit", near);
    });
    map.panTo([b.lat, b.lng], { animate: true });
    renderTopRight(b);
    renderDrawer();
  }

  // ---------- top bar ----------
  function renderTopRight(b) {
    const el = document.getElementById("topRight");
    if (!b) { el.innerHTML = ""; return; }
    el.innerHTML =
      '<div class="text-[13px] font-extrabold">' + usd(b.price_low_usd) + "–" + usd(b.price_high_usd) +
      '/mo <span class="text-gray-400 font-medium">· ' + vnd(b.price_band.real_median_vnd) + "/th</span></div>" +
      '<div class="text-[12px] text-gray-500">★ ' + b.rating + " · " + b.reviews + " verified reviews</div>";
  }

  function renderViewToggle() {
    document.querySelectorAll("#view-toggle button").forEach((btn) => {
      const on = btn.dataset.view === state.view;
      btn.classList.toggle("on", on);
    });
    document.getElementById("ctaBtn").textContent =
      state.view === "tenant" ? "Get 3 Live Units" : "Xuất B2B Proposal";
  }

  function renderBldTabs() {
    const tabs = [["map", "Map & Location"], ["photos", "Verified Photos"], ["metrics", "Living Metrics"], ["reviews", "Tenant Reviews"]];
    document.getElementById("bld-tabs").innerHTML = tabs.map(
      (t) => '<button data-tab="' + t[0] + '" class="' + (state.bldTab === t[0] ? "on" : "") + '">' + t[1] + "</button>"
    ).join("");
    document.querySelectorAll("#bld-tabs button").forEach((btn) =>
      btn.onclick = () => { state.bldTab = btn.dataset.tab; renderBldTabs(); renderDrawer(); });
  }

  // ---------- pills ----------
  function renderPills() {
    const keys = ["dining", "park", "school", "metro", "coworking"];
    let html = keys.map((k) =>
      '<span class="pill ' + (state.layers[k] ? "on" : "") + '" data-layer="' + k + '">' +
      '<span class="sw" style="background:' + POI_COLOR[k] + '"></span>' + POI_LABEL[k].slice(2) + "</span>"
    ).join("");
    html += '<span class="pill ' + (state.layers.flood ? "on" : "") + '" data-layer="flood">🌊 Flood &amp; Noise</span>';
    const el = document.getElementById("pills");
    el.innerHTML = html;
    el.querySelectorAll(".pill").forEach((p) => p.onclick = () => toggleLayer(p.dataset.layer));
  }

  function toggleLayer(key) {
    state.layers[key] = !state.layers[key];
    if (key === "flood") { renderOverlays(); renderPills(); return; }
    // ẩn/hiện POI loại đó (chỉ ghim đó, KHÔNG đụng markerPane chung)
    Object.values(poiMarkers).forEach((o) => {
      if (o.p.type === key) { const el = o.m.getElement(); if (el) el.style.display = state.layers[key] ? "" : "none"; }
    });
    if (state.selected) selectBuilding(state.selected); // tính lại "lit"
    renderPills();
  }

  function renderOverlays() {
    overlayShapes.forEach((s) => map.removeLayer(s)); overlayShapes.length = 0;
    if (!state.layers.flood) return;
    (D.overlays.flood || []).forEach((f) => overlayShapes.push(
      L.circle([f.lat, f.lng], { radius: f.radius, color: "#0ea5e9", weight: 1, fillColor: "#0ea5e9", fillOpacity: 0.18 })
        .bindTooltip("🌊 " + f.level).addTo(map)));
    (D.overlays.noise || []).forEach((f) => overlayShapes.push(
      L.circle([f.lat, f.lng], { radius: f.radius, color: "#ef4444", weight: 1, fillColor: "#ef4444", fillOpacity: 0.14 })
        .bindTooltip("🔊 " + f.level).addTo(map)));
  }

  // ---------- filters (#2) ----------
  function renderFilters() {
    const segs = [...new Set((D.buildings || []).flatMap((b) => b.segments || []))];
    const el = document.getElementById("filters");
    el.innerHTML =
      '<span class="text-[11px] font-bold text-gray-400 mr-0.5">LỌC</span>' +
      '<select id="f-price" class="text-xs border border-gray-300 rounded-md px-1.5 py-1 bg-white"><option value="0">Mọi giá</option><option value="500">&lt; $500</option><option value="750">&lt; $750</option><option value="1000">&lt; $1000</option></select>' +
      '<select id="f-sub" class="text-xs border border-gray-300 rounded-md px-1.5 py-1 bg-white max-w-[120px]"><option value="">Mọi khu</option>' +
      (D.subzones || []).map((s) => '<option value="' + s.code + '">' + esc(s.name.split("—")[0].trim()) + "</option>").join("") + "</select>" +
      '<select id="f-seg" class="text-xs border border-gray-300 rounded-md px-1.5 py-1 bg-white"><option value="">Mọi loại</option>' +
      segs.map((s) => '<option value="' + s + '">' + (SEG_LABEL[s] || s) + "</option>").join("") + "</select>" +
      '<span class="pill" style="padding:5px 10px;font-size:12px" id="f-deal">⭐ Deal tốt</span>' +
      '<span class="text-[11px] text-gray-400" id="f-count"></span>';
    document.getElementById("f-price").onchange = (e) => { state.filters.priceMax = +e.target.value; applyFilters(); };
    document.getElementById("f-sub").onchange = (e) => { state.filters.subzone = e.target.value; applyFilters(); };
    document.getElementById("f-seg").onchange = (e) => { state.filters.segment = e.target.value; applyFilters(); };
    document.getElementById("f-deal").onclick = (e) => { state.filters.dealOnly = !state.filters.dealOnly; e.target.classList.toggle("on", state.filters.dealOnly); applyFilters(); };
  }

  function applyFilters() {
    const f = state.filters;
    let shown = 0;
    Object.values(bldMarkers).forEach((o) => {
      const b = o.b;
      let ok = true;
      if (f.priceMax && b.median_usd > f.priceMax) ok = false;
      if (f.subzone && b.subzone_code !== f.subzone) ok = false;
      if (f.segment && !(b.segments || []).includes(f.segment)) ok = false;
      if (f.dealOnly && (b.deal_score || 0) < 55) ok = false;
      const el = o.m.getElement(); if (el) el.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    const cnt = document.getElementById("f-count"); if (cnt) cnt.textContent = shown + "/" + D.buildings.length + " tòa";
  }

  // ---------- search ----------
  document.getElementById("search").addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    Object.values(poiMarkers).forEach((o) => {
      const hit = !q || o.p.name.toLowerCase().includes(q) || POI_LABEL[o.p.type].toLowerCase().includes(q);
      const el = o.m.getElement(); if (el) el.style.opacity = hit ? "1" : "0.15";
    });
  });

  // ---------- drawer ----------
  function renderDrawer() {
    const el = document.getElementById("drawer");
    if (!state.selected) {
      el.innerHTML =
        '<div class="p-5"><div class="text-xs font-bold tracking-wide text-gray-400 uppercase">VeriMap · Thảo Điền</div>' +
        '<h1 class="text-xl font-extrabold mt-1">Bản đồ Tình báo Thuê nhà</h1>' +
        '<p class="text-sm text-gray-500 mt-2 leading-relaxed">Chọn một <b>ghim nhà đen</b> trên bản đồ để xem: dữ liệu thật (lọc tin ảo), chỉ số sống thực tế, và trạm kết nối / dòng tiền.</p>' +
        '<div class="card !mx-0 mt-4 bg-gray-50"><div class="text-xs font-bold text-gray-500 uppercase mb-2">' + D.buildings.length + ' tòa nhà trong khu</div>' +
        D.buildings.map((b) => '<div class="kchip cursor-pointer hover:text-[color:var(--ab)]" data-b="' + b.id + '"><span>🏢 ' + esc(b.name) + '</span><span class="font-bold">' + usd(b.median_usd) + "/mo</span></div>").join("") +
        "</div></div>";
      el.querySelectorAll("[data-b]").forEach((x) => x.onclick = () => selectBuilding(x.dataset.b));
      return;
    }
    const b = bldMarkers[state.selected].b;
    const af = b.anti_fake, pb = b.price_band, lv = b.living;
    const maxBand = Math.max(pb.online_fake_vnd, pb.real_median_vnd, pb.real_high_vnd);
    const w = (x) => Math.round((x / maxBand) * 100);

    // header + Deal badge (#3)
    const ds = b.deal_score == null ? 50 : b.deal_score;
    const dcol = ds >= 65 ? "#16a34a" : ds >= 50 ? "#d97706" : "#6b7280";
    let body =
      '<div class="px-4 pt-4 pb-1"><div class="flex items-start justify-between gap-2">' +
      '<div><h2 class="text-lg font-extrabold leading-tight">' + esc(b.name) + '</h2>' +
      '<div class="text-xs text-gray-400 font-mono">' + esc(b.code) + ' · ★ ' + b.rating + ' · ' + b.verified_units + ' căn verified</div></div>' +
      '<span class="tag" style="background:' + dcol + ';color:#fff" title="Deal Score: giá thật vs median khu">⭐ Deal ' + ds + '</span></div></div>';

    if (state.bldTab === "photos") {
      body += '<div class="card"><div class="font-bold text-sm mb-2">📸 Verified Photos</div><div class="grid grid-cols-2 gap-2">' +
        [1, 2, 3, 4].map((i) => '<div class="rounded-lg h-24 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center text-gray-400 text-xs">Ảnh kiểm chứng #' + i + "</div>").join("") +
        '</div><div class="text-[11px] text-gray-400 mt-2">Ảnh do chuyên viên chụp tại hiện trường, chống ảnh "mồi" trên mạng.</div></div>';
    } else if (state.bldTab === "reviews") {
      body += '<div class="card"><div class="font-bold text-sm mb-2">⭐ Tenant Reviews (' + b.reviews + ')</div>' +
        ['"Quản lý tốt, an ninh ổn, nhiều hàng xóm Tây." — Expat tenant', '"Giá thật đúng như VeriMap báo, không bị hớ." — Chị Lan', '"Gần trường quốc tế, tiện cho con." — A. Minh']
          .map((r) => '<div class="text-[13px] text-gray-600 py-2 border-b border-gray-100">★★★★★ ' + esc(r) + "</div>").join("") + "</div>";
    } else if (state.bldTab === "metrics") {
      body += livingBlock(lv, true);
    } else {
      // map & location (mặc định) = 3 khối tình báo
      body +=
        '<div class="card"><div class="font-bold text-sm flex items-center gap-1.5">🛡️ Anti-Fake Data Filter</div>' +
        '<p class="text-[13px] text-gray-600 mt-1.5 leading-relaxed">Đã quét <b>' + af.scanned + '</b> tin rao vặt tại tòa → loại <b class="text-red-500">' + af.fake_removed + '</b> tin ảo/giá mồi (&lt; ' + vnd(af.bait_threshold_vnd) + ') → giữ <b class="text-green-600">' + af.real_kept + '</b> căn trống THẬT hôm nay.</p>' +
        '<div class="mt-3 text-[11px] font-bold text-gray-500 uppercase">Price band: ảo trên mạng vs giao dịch thật</div>' +
        '<div class="mt-2 space-y-1.5">' +
        bandRow("Giá mồi online", pb.online_fake_vnd, w(pb.online_fake_vnd), "#f87171") +
        bandRow("Giá thật trung vị", pb.real_median_vnd, w(pb.real_median_vnd), "#22c55e") +
        bandRow("Giá thật cao", pb.real_high_vnd, w(pb.real_high_vnd), "#16a34a") +
        "</div></div>";
      if (b.market) {
        const mk = b.market;
        body += '<div class="card" style="border-color:#e0e7ff;background:#f6f8ff"><div class="font-bold text-sm">📡 Tín hiệu thị trường khu <span class="text-[10px] text-gray-400 font-normal">(Social/bds)</span></div>' +
          '<p class="text-[12px] text-gray-600 mt-1.5 leading-relaxed"><b class="text-green-600">' + mk.yield + '</b> tín hiệu CHO THUÊ · <b class="text-red-500">' + mk.distress + '</b> CẮT LỖ · tổng <b>' + mk.total + '</b> tín hiệu social. Sức khoẻ khu: <b style="color:' + (mk.net > 0 ? '#16a34a' : '#ef4444') + '">' + (mk.net > 0 ? '+' : '') + mk.net + '</b>.</p></div>';
      }
      body += livingBlock(lv, false);
      body += monetBlock(b);
    }
    el.innerHTML = body;
    wireDrawer();
  }

  function livingBlock(lv, expanded) {
    return '<div class="card"><div class="font-bold text-sm">🏠 Chỉ số Sống Thực tế</div><div class="mt-2">' +
      kc("Phí quản lý", vnd(lv.mgmt_fee_vnd) + "/m²") + kc("Gửi ô tô", vnd(lv.parking_car_vnd) + "/th") +
      kc("Gửi xe máy", vnd(lv.parking_bike_vnd) + "/th") + kc("Ngập khi mưa lớn", lv.flood_risk) +
      kc("Hướng nắng", lv.sun) + kc("Tỷ lệ cư dân Expat", lv.expat_ratio + "%") +
      (expanded ? kc("Walkability", "POI sáng trong bán kính 800m trên map") : "") + "</div></div>";
  }

  function monetBlock(b) {
    if (state.view === "tenant") {
      const sp = b.specialist;
      return '<div class="card" style="border-color:#fde2e8"><div class="font-bold text-sm flex items-center gap-1.5">🤝 Trạm Kết nối</div>' +
        '<div class="mt-2 flex items-center gap-3 p-2.5 rounded-xl bg-rose-50">' +
        '<div class="w-10 h-10 rounded-full bg-[color:var(--ab)] text-white flex items-center justify-center font-bold">' + esc(sp.name[0]) + "</div>" +
        '<div class="min-w-0"><div class="font-bold text-sm">' + esc(sp.name) + ' <span class="tag" style="background:#dcfce7;color:#15803d">✓ Verified</span></div>' +
        '<div class="text-[12px] text-gray-500">Building Specialist · ' + esc(sp.langs) + ' · ★ ' + sp.rating + "</div></div></div>" +
        '<button class="btn-ab w-full mt-3" data-act="book">💬 Gửi yêu cầu xem (Zalo/WhatsApp)</button>' +
        '<button class="btn-ghost w-full mt-2" data-act="unlock">🔓 Mở khóa tin Chính chủ Pass gấp — 49.000đ</button></div>';
    }
    // B2B revenue view
    const free = !b.b2b.exclusive_to;
    return '<div class="card" style="border-color:#dbeafe;background:#f8fbff"><div class="font-bold text-sm flex items-center gap-1.5">💰 Trạm Ra tiền (B2B)</div><div class="mt-2">' +
      kc("Slot QC tòa nhà", b.b2b.slot_status) +
      kc("Phí thuê slot", vnd(b.b2b.monthly_fee_vnd) + "/tháng") +
      kc("Lead đã chuyển giao (tháng)", b.b2b.leads_month + " leads") +
      kc("Độc quyền", b.b2b.exclusive_to || "— (đang trống)") + "</div>" +
      '<button class="btn-ab w-full mt-3" data-act="proposal">🗺️ Tạo B2B Map Proposal Link</button>' +
      '<div class="text-[11px] text-gray-500 mt-1.5 text-center">Chọn 3 tòa → link bản đồ cá nhân hóa cho khách Tây · SaaS 299.000đ/tháng</div>' +
      (free ? '<button class="btn-ghost w-full mt-2" data-act="rentslot">📢 Thuê slot độc quyền tòa này — ' + vnd(b.b2b.monthly_fee_vnd) + "/th</button>" : "") +
      "</div>";
  }

  function wireDrawer() {
    document.querySelectorAll("#drawer [data-act]").forEach((btn) => btn.onclick = () => {
      const msg = {
        book: "✅ (Demo) Đã gửi yêu cầu xem nhà tới Building Specialist qua Zalo/WhatsApp.",
        unlock: "🔓 (Demo) Đã mở khóa 1 tin Chính chủ Pass gấp (phí 49.000đ).",
        proposal: "🗺️ (Demo) Đã tạo B2B Map Proposal Link — tick 3 tòa để gửi khách Tây.",
        rentslot: "📢 (Demo) Mở form thuê slot quảng cáo độc quyền tòa nhà.",
      }[btn.dataset.act];
      toast(msg);
    });
  }

  // ---------- small render utils ----------
  const kc = (k, v) => '<div class="kchip"><span class="text-gray-500">' + k + '</span><span class="font-semibold">' + esc(v) + "</span></div>";
  const bandRow = (label, v, pct, color) =>
    '<div><div class="flex justify-between text-[12px] mb-0.5"><span class="text-gray-500">' + label + '</span><span class="font-bold">' + vnd(v) + '/th</span></div>' +
    '<div class="bar"><span style="width:' + pct + '%;background:' + color + '"></span></div></div>';

  function toast(m) {
    let t = document.getElementById("_toast");
    if (!t) { t = document.createElement("div"); t.id = "_toast"; t.className = "fixed bottom-5 left-1/2 -translate-x-1/2 z-[999] bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-2xl"; document.body.appendChild(t); }
    t.textContent = m; t.style.opacity = "1";
    clearTimeout(t._h); t._h = setTimeout(() => (t.style.opacity = "0"), 3200);
  }

  // ---------- view toggle wiring ----------
  document.querySelectorAll("#view-toggle button").forEach((btn) => btn.onclick = () => {
    state.view = btn.dataset.view; renderViewToggle(); renderDrawer();
  });
  document.getElementById("ctaBtn").onclick = () => toast(state.view === "tenant"
    ? "🏡 (Demo) Nhận 3 căn trống THẬT đã kiểm chứng từ Verified Partner."
    : "🗺️ (Demo) Xuất B2B Map Proposal cho khách doanh nghiệp.");

  // ---------- init ----------
  if (window.lucide) lucide.createIcons();
  renderViewToggle(); renderBldTabs(); renderPills(); renderFilters(); applyFilters(); renderDrawer();
})();
