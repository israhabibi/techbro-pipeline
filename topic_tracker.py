#!/usr/bin/env python3
"""
Topic Tracker: extract + agregasi topik hangat dari tweet techbro Indonesia.
Baca semua feed_*.json (akumulasi), kirim ke adaCODE 1x/hari -> topics_YYYYMMDD.json
Biaya: 1 API call per run (bukan per tweet) -> quota aman.
"""
import json, os, glob, datetime, httpx

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
KEY = os.environ.get("ADACODE_API_KEY", "")
MODEL = os.environ.get("ADACODE_MODEL", "claude-sonnet-4-6")
API = "https://api.adacode.ai/v1/chat/completions"


def parse_day(created_at):
    """Twitter format -> YYYY-MM-DD (atau '' kalau gagal)."""
    try:
        return datetime.datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d")
    except Exception:
        return ""


def collect_tweets(days=14):
    """Ambil tweet techbro dari N hari terakhir feed_*.json, sertakan field day."""
    files = sorted(glob.glob(os.path.join(DATA, "feed_*.json")))
    tweets = []
    seen = set()
    for f in files[-days:]:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for t in d.get("tweets", []):
            if not t.get("is_techbro_id"):
                continue
            key = t.get("id")
            if key in seen:
                continue
            seen.add(key)
            tweets.append({
                "user": t.get("user", ""),
                "day": parse_day(t.get("created_at", "")),
                "text": (t.get("text") or "").replace("\n", " ").strip()[:400],
            })
    return tweets


def extract_topics(tweets):
    if not tweets:
        return []
    # batasi ~60 tweet teratas biar prompt gak kepanjangan
    sample = tweets[:60]
    lines = "\n".join(f"[{t['day']}] @{t['user']}: {t['text']}" for t in sample)
    prompt = (
        "Berikut kumpulan tweet dari komunitas techbro Indonesia (beberapa hari terakhir). "
        "Setiap baris diawali [YYYY-MM-DD] yang menunjukkan hari tweet itu diposting.\n"
        "Tugasmu: EXTRACT dan AGREGASI topik-topik hangat yang muncul. "
        "Kelompokkan tweet serupa ke topik yang sama. Untuk tiap topik, beri:\n"
        "1. nama topik (singkat, 2-4 kata)\n"
        "2. jumlah tweet terkait (perkiraan)\n"
        "3. 1-2 kalimat narasi (gaya santai Indo lo-gue) yang rangkum perdebatan/isu di topik itu\n"
        "4. list handle yang terlibat (maks 5)\n"
        "5. list hari (YYYY-MM-DD) di mana topik ini muncul, diambil dari prefix [tanggal] tiap tweet (field 'days')\n\n"
        "Balas HANYA dalam JSON array, tanpa teks lain, format:\n"
        '[{"topic":"...","count":N,"summary":"...","handles":["@a","@b"],"days":["2026-08-09","2026-08-10"]}, ...]\n\n'
        "Tweets:\n" + lines
    )
    try:
        r = httpx.post(API, headers={"Authorization": f"Bearer {KEY}",
                        "Content-Type": "application/json"},
                       json={"model": MODEL, "messages": [
                           {"role": "system", "content": "Kamu agregator topik techbro ID. Balas JSON saja."},
                           {"role": "user", "content": prompt}],
                           "max_tokens": 1000, "temperature": 0.3}, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # ambil JSON dalam teks
        start = content.find("[")
        end = content.rfind("]") + 1
        return json.loads(content[start:end])
    except Exception as e:
        print(f"[warn] extract gagal: {e}", file=__import__("sys").stderr)
        return []


def main():
    today = datetime.datetime.utcnow().strftime("%Y%m%d")
    tweets = collect_tweets(days=14)
    print(f"[tracker] collected {len(tweets)} techbro tweets (14 hari)")
    topics = extract_topics(tweets)
    out = {
        "date": today,
        "total_tweets_scanned": len(tweets),
        "topics": topics,
    }
    fname = os.path.join(DATA, f"topics_{today}.json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Saved -> {fname} ({len(topics)} topik)")
    for t in topics[:5]:
        print(f"  • {t.get('topic')} ({t.get('count')}) — {t.get('summary','')[:60]}")


if __name__ == "__main__":
    main()
