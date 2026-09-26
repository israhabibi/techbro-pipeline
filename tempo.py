#!/usr/bin/env python3
"""
Tempo.co RSS fetcher -> list of articles.
Menulis hasil ke data/tempo_YYYYMMDD.json
"""
import json, os, sys, datetime, urllib.request, xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

TEMPO_FEEDS = {
    "nasional": "https://rss.tempo.co/nasional",
    "bisnis": "https://rss.tempo.co/bisnis",
    "tekno": "https://rss.tempo.co/tekno",
}

UA = "Mozilla/5.0 (compatible; TechbroDigest/1.0)"


def fetch_feed(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8", "replace")
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        def txt(tag):
            e = it.find(tag)
            return (e.text or "").strip() if e is not None else ""
        # content:encoded for full body
        body = ""
        ce = it.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        if ce is not None:
            body = (ce.text or "").strip()
        items.append({
            "source": f"tempo:{name}",
            "title": txt("title"),
            "link": txt("link"),
            "pubDate": txt("pubDate"),
            "description": txt("description") or body[:500],
            "body": (body or txt("description"))[:2000],
        })
    return items


def main():
    all_items = []
    for name, url in TEMPO_FEEDS.items():
        try:
            items = fetch_feed(name, url)
            print(f"[tempo/{name}] {len(items)} items")
            all_items.extend(items)
        except Exception as e:
            print(f"[warn] tempo/{name} failed: {e}", file=sys.stderr)
    out = {
        "scanned_at": datetime.datetime.utcnow().isoformat() + "Z",
        "source": "tempo.co RSS",
        "count": len(all_items),
        "articles": all_items,
    }
    fname = os.path.join(DATA, "tempo_" + datetime.datetime.utcnow().strftime("%Y%m%d") + ".json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {fname}  ({len(all_items)} articles)")
    # preview
    for a in all_items[:5]:
        print(f"  [{a['source']}] {a['title'][:70]}")


if __name__ == "__main__":
    main()
