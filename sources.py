#!/usr/bin/env python3
"""
Collector sumber tambahan untuk digest:
  1. Google News RSS per keyword -> cover semua media (Detik/Kompas/CNN/Tirto/Tempo)
  2. Tempo RSS
Timeline Twitter akun lo sendiri sudah di-handle scan.py (feed_*.json).
Hasil ditulis ke data/sources_YYYYMMDD.json (per-hari, TIDAK overwrite feed/tempo).
"""
import json, os, sys, datetime, urllib.request, urllib.parse, xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# Keyword yang mau dipantau (bisa lo edit)
KEYWORDS = ["Prabowo", "IKN", "duit rakyat", "efek domino", "subsidi", "prabowo ekonomi"]

# Seed akun Twitter (selain techbro, buat "suara lain")
TWITTER_SEED = [
    "prabowo", "ganjarpranowo", "KompasTV", "cnnindonesia", "tempodotco",
    "tirto_id", "detikcom", "bank_indonesia", "KemenkeuRI", "BappenasRI",
]


def fetch_google_news(q, max_items=12):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=id&gl=ID&ceid=ID:id"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8", "replace")
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        def txt(tag):
            e = it.find(tag)
            return (e.text or "").strip() if e is not None else ""
        src = ""
        ce = it.find("{http://purl.org/dc/elements/1.1/}creator")
        if ce is not None:
            src = (ce.text or "").strip()
        items.append({
            "source": f"news:{q}",
            "title": txt("title"),
            "link": txt("link"),
            "pubDate": txt("pubDate"),
            "creator": src,
        })
        if len(items) >= max_items:
            break
    return items


def fetch_tempo_rss():
    feeds = {
        "nasional": "https://rss.tempo.co/nasional",
        "bisnis": "https://rss.tempo.co/bisnis",
        "tekno": "https://rss.tempo.co/tekno",
    }
    out = []
    for name, url in feeds.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read().decode("utf-8", "replace")
            root = ET.fromstring(raw)
            for it in root.iter("item"):
                def txt(tag):
                    e = it.find(tag)
                    return (e.text or "").strip() if e is not None else ""
                out.append({"source": f"tempo:{name}", "title": txt("title"),
                            "link": txt("link"), "pubDate": txt("pubDate")})
        except Exception as e:
            print(f"[warn] tempo/{name}: {e}", file=sys.stderr)
    return out


def main():
    today = datetime.datetime.utcnow().strftime("%Y%m%d")
    out = {"date": today, "keywords": {}, "tempo": []}

    # 1. Google News per keyword
    for kw in KEYWORDS:
        try:
            items = fetch_google_news(kw)
            out["keywords"][kw] = items
            print(f"[news/{kw}] {len(items)} items")
        except Exception as e:
            print(f"[warn] news/{kw}: {e}", file=sys.stderr)
            out["keywords"][kw] = []

    # 2. Tempo RSS
    try:
        out["tempo"] = fetch_tempo_rss()
        print(f"[tempo] {len(out['tempo'])} items")
    except Exception as e:
        print(f"[warn] tempo: {e}", file=sys.stderr)

    fname = os.path.join(DATA, f"sources_{today}.json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {fname}")
    print(f"Keywords: {sum(len(v) for v in out['keywords'].values())} | Tempo: {len(out['tempo'])}")


if __name__ == "__main__":
    main()

