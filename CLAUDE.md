# RENT — CLAUDE (chuẩn FDE 6 Trụ Cột)

Nạp đầu phiên: **CLAUDE.md → BLUEPRINT.md → docs/** (6 trụ). Red-team mặc định · Why-trước-How · Zero-hallucination.

## 6 Trụ (chi tiết ở `docs/`)
- **1 PM + 6 Adoption** → `docs/01-problem-and-adoption.md`
- **2 Data** → `docs/02-ontology-and-ssot.md` _(chuẩn chung: `ssot-registry/00-master-ontology.md`)_
- **3 Dev + 5 Ops/FinOps** → `docs/03-arch-and-finops.md` _(stack: `ssot-registry/02-approved-stack.md`)_
- **4 Governance** → `docs/04-legal-and-security.md` _(đối chiếu `LEGAL/02_STRUCTURED_RULES/`)_

## LUẬT NHÀ (nguồn: `ssot-registry/01-global-guardrails.md`)
`[ZONE]` đủ In/Out/Status · LOCKED cấm sửa nếu không có lệnh · Khiên `pre-commit` bật (`core.hooksPath=hooks`) · secret ở `_VAULT/`, repo chỉ `.env.example` · **logic lõi phải có `evals/` (≥1 golden case)**.

## LỆNH CHỦ
- **"check hệ thống"** — tự soi LUẬT NHÀ + chạy `evals/` + SỬA vi phạm trong lãnh thổ.
- **"show hệ thống"** — xuất X-quang gọn (khung xương, 0 data) trình Control Center.

## Quan sát (chạy TỪ HUB)
`python <hub>/tools/zones.py <path>` · `bridge.py --xray <tên>` · `fde_audit.py` (chấm 6 trụ).

