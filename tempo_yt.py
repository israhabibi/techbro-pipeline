#!/usr/bin/env python3
"""
Tempo YouTube fetcher -> latest videos from Tempo channels (RSS, no API key).
Writes data/tempo_yt_YYYYMMDD.json with video METADATA only
(transcripts are pulled later by the cron agent via web tool).
"""
import json, os, sys, datetime, urllib.request, xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

# Tempo channels (Bocor Alus Politik + Tempo TV both live under Tempodotco)
CHANNELS = {
    "tempodotco": "UC3QRoNY-nYDTNSv-1dR0P-g",
}

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}

UA = "Mozilla/5.0 (compatible; TechbroDigest/1.0)"


def fetch_channel(name, channel_id, max_n=5):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read().decode("utf-8", "replace")
    root = ET.fromstring(raw)
    out = []
    for e in root.findall("atom:entry", NS):
        vid = e.find("yt:videoId", NS)
        title = e.find("atom:title", NS)
        pub = e.find("atom:published", NS)
        link = e.find("atom:link", NS)
        out.append({
            "channel": name,
            "video_id": vid.text if vid is not None else "",
            "title": (title.text or "").strip() if title is not None else "",
            "published": pub.text if pub is not None else "",
            "url": f"https://www.youtube.com/watch?v={vid.text}" if vid is not None else (link.get("href") if link is not None else ""),
            "transcript": "",   # filled by cron agent via web tool
            "summary": "",     # filled by cron agent
        })
        if len(out) >= max_n:
            break
    return out


def main():
    all_v = []
    for name, cid in CHANNELS.items():
        try:
            vs = fetch_channel(name, cid)
            print(f"[yt/{name}] {len(vs)} videos")
            all_v.extend(vs)
        except Exception as e:
            print(f"[warn] yt/{name} failed: {e}", file=sys.stderr)
    out = {
        "scanned_at": datetime.datetime.utcnow().isoformat() + "Z",
        "source": "YouTube Tempo (Tempodotco)",
        "count": len(all_v),
        "videos": all_v,
    }
    fname = os.path.join(DATA, "tempo_yt_" + datetime.datetime.utcnow().strftime("%Y%m%d") + ".json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {fname} ({len(all_v)} videos)")
    for v in all_v[:5]:
        print(f"  - {v['title'][:60]}")


if __name__ == "__main__":
    main()
