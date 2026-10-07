#!/usr/bin/env python3
"""
Topic Tracker: extract + agregasi topik hangat dari tweet techbro Indonesia.
Baca semua feed_*.json (akumulasi), kirim ke adaCODE 1x/hari -> topics_YYYYMMDD.json
Biaya: 1 API call per run (bukan per tweet) -> quota aman.
"""

import datetime
import glob
import json
import os
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

from techbro_pipeline.config import Settings, write_json

DATA = str(Settings.from_env().data_dir)
KEY = os.environ.get("ADACODE_API_KEY", "")
MODEL = os.environ.get("ADACODE_MODEL", "adacode-2.0")
API = "https://api.adacode.ai/v1/chat/completions"
LOCAL_TZ = ZoneInfo("Asia/Jakarta")
WINDOW_HOURS = 24


def parse_timestamp(created_at):
    try:
        return datetime.datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y").astimezone(
            LOCAL_TZ
        )
    except Exception:
        return None


def collect_tweets(window_hours=WINDOW_HOURS):
    """Ambil tweet techbro dalam jendela waktu terakhir, berdasarkan waktu Jakarta."""
    files = sorted(glob.glob(os.path.join(DATA, "feed", "feed_*.json")))[-14:]
    now = datetime.datetime.now(LOCAL_TZ)
    cutoff = now - datetime.timedelta(hours=window_hours)
    tweets = []
    seen = set()
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        for t in d.get("tweets", []):
            if not t.get("is_techbro_id") or not t.get("is_tech_tweet"):
                continue
            created = parse_timestamp(t.get("created_at", ""))
            if not created or not cutoff <= created <= now:
                continue
            key = t.get("id")
            if key in seen:
                continue
            seen.add(key)
            tweets.append(
                {
                    "user": t.get("user", ""),
                    "day": created.strftime("%Y-%m-%d %H:%M WIB"),
                    "text": (t.get("text") or "").replace("\n", " ").strip()[:400],
                    "created_at": created,
                }
            )
    tweets.sort(key=lambda tweet: tweet["created_at"], reverse=True)
    for tweet in tweets:
        del tweet["created_at"]
    return tweets


def extract_topics(tweets):
    if not tweets:
        return []
    if not KEY:
        print(
            "[warn] ADACODE_API_KEY belum di-set; ekstraksi topik dilewati.",
            file=__import__("sys").stderr,
        )
        return []
    # batasi ~60 tweet teratas biar prompt gak kepanjangan
    sample = tweets[:60]
    lines = "\n".join(f"[{t['day']}] @{t['user']}: {t['text']}" for t in sample)
    prompt = (
        "Berikut kumpulan tweet dari komunitas techbro Indonesia dalam 24 jam terakhir "
        "(waktu Asia/Jakarta). Setiap baris diawali waktu lokal saat tweet diposting.\n"
        "Tugasmu: buat brief editorial yang membantu pembaca memahami obrolan, bukan sekadar daftar topik. "
        "Kelompokkan tweet serupa. Pisahkan fakta yang tampak di tweet dari konteks umum; jangan mengarang angka, klaim, atau konsensus. "
        "Kalau menambahkan konteks umum, jelaskan singkat dan hati-hati. Untuk tiap topik, beri:\n"
        "1. nama topik (singkat, 2-4 kata)\n"
        "2. jumlah tweet terkait (perkiraan)\n"
        "3. summary: jelaskan apa yang sedang diperdebatkan/dibangun dan sudut pandang yang muncul, 2 kalimat\n"
        "4. context: konteks dasar agar pembaca non-ahli paham istilah atau latar isu, 1 kalimat; bila tidak yakin, tulis null\n"
        "5. value_added: analisis singkat kenapa isu ini penting atau trade-off yang perlu diperhatikan, 1 kalimat; tandai sebagai analisis, bukan fakta tweet\n"
        "6. list handle yang terlibat (maks 5)\n"
        "7. list tanggal (YYYY-MM-DD) saat topik muncul, berdasarkan waktu pada tiap baris (field 'days')\n\n"
        "Balas HANYA dalam JSON array, tanpa teks lain, format:\n"
        '[{"topic":"...","count":N,"summary":"...","context":"...","value_added":"...","handles":["@a","@b"],"days":["2026-08-09"]}, ...]\n\n'
        "Tweets:\n" + lines
    )
    try:
        payload = json.dumps(
            {
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Kamu agregator topik techbro ID. Balas JSON saja.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2400,
                "temperature": 0.3,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            API,
            data=payload,
            headers={
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        # ambil JSON dalam teks
        start = content.find("[")
        end = content.rfind("]") + 1
        topics = json.loads(content[start:end])
        if not isinstance(topics, list) or any(
            not isinstance(topic, dict)
            or not isinstance(topic.get("topic"), str)
            or not topic["topic"].strip()
            or len(topic["topic"]) > 160
            or not isinstance(topic.get("count"), int)
            or isinstance(topic["count"], bool)
            or topic["count"] < 0
            or not isinstance(topic.get("summary"), str)
            or any(
                topic.get(field) is not None and not isinstance(topic[field], str)
                for field in ("context", "value_added")
            )
            or any(
                not isinstance(topic.get(field, []), list)
                or any(not isinstance(value, str) for value in topic.get(field, []))
                for field in ("handles", "days")
            )
            for topic in topics
        ):
            raise ValueError("Invalid topic response schema")
        return topics
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace").strip()[:400]
        print(
            f"[warn] extract gagal (HTTP {e.code}): {detail or e.reason}",
            file=__import__("sys").stderr,
        )
        return []
    except Exception as e:
        print(f"[warn] extract gagal: {e}", file=__import__("sys").stderr)
        return []


def main():
    today = datetime.datetime.now(LOCAL_TZ).strftime("%Y%m%d")
    tweets = collect_tweets()
    print(f"[tracker] collected {len(tweets)} techbro tweets (24 jam terakhir)")
    topics = extract_topics(tweets)
    if tweets and not topics:
        print(
            "[warn] tidak ada hasil topik valid; file topics lama dipertahankan",
            file=__import__("sys").stderr,
        )
        return 1
    out = {
        "date": today,
        "window_hours": WINDOW_HOURS,
        "total_tweets_scanned": len(tweets),
        "topics": topics,
    }
    fname = os.path.join(DATA, "topics", f"topics_{today}.json")
    write_json(fname, out)
    print(f"Saved -> {fname} ({len(topics)} topik)")
    for t in topics[:5]:
        print(f"  • {t.get('topic')} ({t.get('count')}) — {t.get('summary', '')[:60]}")


if __name__ == "__main__":
    raise SystemExit(main())
