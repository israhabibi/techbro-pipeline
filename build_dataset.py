#!/usr/bin/env python3
"""
Build Kaggle-ready dataset dari data techbro.
Output:
  dataset/techbro_tweets.csv  -> 1 baris per tweet techbro (akumulasi semua feed_*.json)
  dataset/techbro_topics.csv  -> agregasi topik hangat (dari topics_*.json terbaru)
  dataset/README.md           -> deskripsi dataset

Usage:
  python3 build_dataset.py            # semua data
  python3 build_dataset.py --month 2026-07   # cuma tweet bulan tertentu
"""
import json, os, glob, csv, datetime, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "dataset")
os.makedirs(OUT, exist_ok=True)


def parse_date(created_at):
    """Twitter format: 'Wed Oct 10 20:19:24 +0000 2018' -> (YYYY-MM-DD, YYYY-MM)"""
    try:
        dt = datetime.datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m")
    except Exception:
        return "", ""


def build_tweets(month=None):
    rows = []
    seen = set()
    for f in sorted(glob.glob(os.path.join(DATA, "feed_*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for t in d.get("tweets", []):
            if not t.get("is_techbro_id"):
                continue
            tid = t.get("id")
            if tid in seen:
                continue
            date_iso, ym = parse_date(t.get("created_at", ""))
            if month and ym != month:
                continue
            seen.add(tid)
            rows.append({
                "tweet_id": tid,
                "day": date_iso,
                "user_handle": (t.get("user") or "").lstrip("@"),
                "text": (t.get("text") or "").replace("\n", " ").strip(),
                "created_at": t.get("created_at", ""),
                "user_score": t.get("user_score", 0),
                "reasons": ";".join(t.get("user_reasons", [])),
            })
    rows.sort(key=lambda r: (r["day"], r["user_handle"]))
    path = os.path.join(OUT, "techbro_tweets.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["tweet_id", "day", "user_handle",
                                           "text", "created_at", "user_score", "reasons"])
        w.writeheader()
        w.writerows(rows)
    return rows


def build_activity(month=None):
    """1 baris per (hari, user) -> gampang groupby/day-user nanti."""
    tweets = build_tweets(month)
    agg = {}
    for t in tweets:
        if month and not t["day"].startswith(month):
            continue
        key = (t["day"], t["user_handle"])
        a = agg.setdefault(key, {"day": t["day"], "user_handle": t["user_handle"],
                                 "tweet_count": 0, "max_score": 0, "samples": []})
        a["tweet_count"] += 1
        a["max_score"] = max(a["max_score"], t["user_score"])
        if len(a["samples"]) < 2:
            a["samples"].append(t["text"][:120])
    rows = [{"day": k[0], "user_handle": k[1], "tweet_count": v["tweet_count"],
             "max_score": v["max_score"], "sample_texts": " | ".join(v["samples"])}
            for k, v in agg.items()]
    rows.sort(key=lambda r: (r["day"], r["user_handle"]))
    path = os.path.join(OUT, "techbro_activity.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["day", "user_handle", "tweet_count",
                                           "max_score", "sample_texts"])
        w.writeheader()
        w.writerows(rows)
    return rows


def build_topics():
    files = sorted(glob.glob(os.path.join(DATA, "topics_*.json")))
    if not files:
        return []
    d = json.load(open(files[-1]))
    rows = []
    for t in d.get("topics", []):
        rows.append({
            "topic": t.get("topic", ""),
            "tweet_count": t.get("count", 0),
            "summary": (t.get("summary") or "").replace("\n", " ").strip(),
            "handles": " ".join(t.get("handles", [])),
            "days": " ".join(t.get("days", [])),
        })
    path = os.path.join(OUT, "techbro_topics.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["topic", "tweet_count", "summary", "handles", "days"])
        w.writeheader()
        w.writerows(rows)
    return rows


def write_readme(n_tweets, n_topics, n_activity, month=None):
    scope = f" (bulan {month})" if month else " (akumulasi semua waktu)"
    md = f"""# Techbro Twitter Indonesia Dataset{scope}

Kumpulan tweet dari komunitas "techbro" Indonesia (engineer/developer/founder
teknologi Tanah Air) yang dikumpulkan harian lewat timeline X (Twitter).

## Files
- `techbro_tweets.csv` — {n_tweets} tweet techbro{scope}, 1 baris per tweet, kolom:
  - `tweet_id`, `day`, `user_handle`, `text`, `created_at`, `user_score`, `reasons`
- `techbro_activity.csv` — {n_activity} baris (1 per hari × user), kolom:
  - `day`, `user_handle`, `tweet_count`, `max_score`, `sample_texts`
- `techbro_topics.csv` — {n_topics} topik hangat teragregasi (14 hari terakhir), kolom:
  - `topic`, `tweet_count`, `summary`, `handles`, `days`

## Method
Tweet diklasifikasi sebagai "techbro ID" lewat aturan: reference handle + lokasi
Indonesia + keyword teknologi (engineer/developer/founder/cto/dll). Topik diekstrak
dan diagregasi pakai model AI (Claude via adaCODE) dari teks tweet.

## Notes
- Data publik dari X (Twitter). Handle adalah akun publik.
- Dibuat untuk riset NLP/sosiolinguistik komunitas tech Indonesia.
- Tidak ada konten pribadi di luar apa yang sudah publik di X.
"""
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="filter YYYY-MM (mis. 2026-07)")
    args = ap.parse_args()
    tweets = build_tweets(args.month)
    topics = build_topics()
    activity = build_activity(args.month)
    write_readme(len(tweets), len(topics), len(activity), args.month)
    tag = f" [{args.month}]" if args.month else ""
    print(f"[dataset{tag}] tweets: {len(tweets)} -> dataset/techbro_tweets.csv")
    print(f"[dataset] topics: {len(topics)} -> dataset/techbro_topics.csv")
    print(f"[dataset] activity (day x user): {len(activity)} -> dataset/techbro_activity.csv")
    print(f"[dataset] README.md written")
    if tweets:
        print("Sample:", tweets[0]["day"], "@" + tweets[0]["user_handle"], tweets[0]["text"][:50])
