# -*- coding: utf-8 -*-
"""vault_loader.py — nạp _VAULT/<slug>.env vào os.environ (két ngoài repo, utf-8-sig chịu BOM)."""
import os
from pathlib import Path


def _find_vault(slug: str):
    here = Path(__file__).resolve()
    for d in (here.parent, *here.parents):
        cand = d / "_VAULT" / f"{slug}.env"
        if cand.exists():
            return cand
    return None


def load(slug: str = "rent") -> bool:
    f = _find_vault(slug)
    if not f:
        return False
    for raw in f.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
    return True
