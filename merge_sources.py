#!/usr/bin/env python3
"""
Slice 3: gabung sources_*.json ke digest_*.json.
Tambah section: "pantauan" (keyword news + tempo ekstra).
Tidak mengubah section techbro/tempo/pinggir_jurang yang sudah ada.
"""
import json, os, glob, datetime, sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
today = datetime.datetime.utcnow().strftime("%Y%m%d")

if os.environ.get("ENABLE_SUPPLEMENTAL_RSS", "").lower() not in {"1", "true", "yes"}:
    print("[skip] supplemental RSS merge disabled; set ENABLE_SUPPLEMENTAL_RSS=1 to enable")
    raise SystemExit(0)

def _latest(prefix):
    fs = sorted(glob.glob(os.path.join(DATA, prefix, f"{prefix}_*.json")))
    return fs[-1] if fs else None

src_path = _latest("sources")
dig_path = _latest("digest")
if not src_path or not dig_path:
    print("Sumber atau digest belum ada.")
    raise SystemExit(1)

sources = json.load(open(src_path))
digest = json.load(open(dig_path))

# Build "pantauan" section
pantauan = {"keywords": {}, "tempo_extra": []}
for kw, items in sources.get("keywords", {}).items():
    pantauan["keywords"][kw] = [
        {"title": i.get("title", ""), "source": i.get("source", ""), "link": i.get("link", "")}
        for i in items[:8]
    ]
pantauan["tempo_extra"] = [
    {"title": i.get("title", ""), "link": i.get("link", ""), "source": i.get("source", "")}
    for i in sources.get("tempo", [])[:15]
]

digest["pantauan"] = pantauan

with open(dig_path, "w") as f:
    json.dump(digest, f, indent=2, ensure_ascii=False)
print(f"Merged -> {dig_path}")
print(f"Pantauan keywords: {len(pantauan['keywords'])} | Tempo extra: {len(pantauan['tempo_extra'])}")
