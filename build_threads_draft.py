#!/usr/bin/env python3
"""Build a ready-to-review Threads post from the latest techbro topic summary."""
import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def latest_topics_file():
    files = sorted(glob.glob(os.path.join(DATA, "topics", "topics_*.json")))
    return files[-1] if files else None


def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def sentences(text):
    """Return complete sentence units; never clip a sentence to fit a post."""
    text = clean(text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def make_parts(data):
    topics = data.get("topics") or []
    def editorial_score(item):
        title = (item.get("topic") or "").lower()
        # Keep the daily thread focused on engineering/building, not just
        # announcements or whatever happened to have the most mentions.
        priority = {
            "agent": 6, "rust": 4, "observability": 4,
            "elevenlabs": 3, "code review": 2, "engine": 2,
            "bootcamp": -2, "cohort": -2, "ekspektasi": -3,
        }
        return int(item.get("count", 0) or 0) * 2 + sum(
            weight for keyword, weight in priority.items() if keyword in title
        )

    topics = sorted(topics, key=editorial_score, reverse=True)[:4]
    if not topics:
        return []

    window = data.get("window_hours", 24)
    period = f"{window} jam terakhir"
    scanned = data.get("total_tweets_scanned", 0)
    parts = [{
        "kind": "opening",
        "text": (
            f"Obrolan tech di X — {period}. Dari {scanned} tweet yang dipantau, "
            "ini isu yang paling ramai, apa konteksnya, dan kenapa layak diperhatikan."
        ),
    }]
    for item in topics:
        title = (item.get("topic") or "Topik techbro").strip()
        summary = clean(item.get("summary"))
        context = clean(item.get("context"))
        value = clean(item.get("value_added"))
        handles = [h if h.startswith("@") else "@" + h
                   for h in (item.get("handles") or [])[:4] if h]
        count = item.get("count")
        line = f"{title}."
        prefix = "1/6 — "  # reserve room for the actual part number
        candidates = []
        candidates.extend(("", sentence) for sentence in sentences(summary))
        candidates.extend(("Konteks: ", sentence) for sentence in sentences(context))
        candidates.extend(("Analisis: ", sentence)
                          for sentence in sentences(value.removeprefix("Analisis: ")))
        for label, sentence in candidates:
            addition = f" {label}{sentence}"
            if len(prefix + line + addition) <= 500:
                line += addition

        # Attribution is useful, but never let it push a complete sentence over
        # Threads' 500-character limit.
        for suffix in ([f" · {count} tweet"] if count else []) + ([" · " + ", ".join(handles[:3])] if handles else []):
            if len(prefix + line + suffix) <= 500:
                line += suffix
        parts.append({"kind": "topic", "topic": title, "text": line})

    parts.append({
        "kind": "closing",
        "text": "Bacaan kami: yang menarik bukan cuma apa yang ramai, tapi trade-off di baliknya—biaya, kecepatan, dan siapa yang benar-benar terbantu. Mana isu yang paling berpengaruh ke cara kita bikin software?",
    })
    total = len(parts)
    for index, part in enumerate(parts, start=1):
        part["number"] = index
        part["text"] = f"{index}/{total} — {part['text']}"
    return parts


def main():
    source = latest_topics_file()
    if not source:
        print("[skip] belum ada topics_*.json; jalankan topic_tracker.py dulu")
        return 0

    with open(source, encoding="utf-8") as fh:
        data = json.load(fh)
    parts = make_parts(data)
    if not parts:
        print(f"[skip] {source} belum berisi topik; draft tidak dibuat")
        return 0

    date = data.get("date") or os.path.basename(source).removeprefix("topics_").removesuffix(".json")
    draft = {
        "date": date,
        "window_hours": data.get("window_hours", 24),
        "source_tweets": data.get("total_tweets_scanned", 0),
        "status": "draft",
        "parts": parts,
    }
    json_path = os.path.join(DATA, "threads", f"threads_draft_{date}.json")
    text_path = os.path.join(DATA, "threads", f"threads_draft_{date}.txt")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(draft, fh, ensure_ascii=False, indent=2)
    with open(text_path, "w", encoding="utf-8") as fh:
        fh.write("\n\n---\n\n".join(part["text"] for part in parts) + "\n")
    print(f"[draft] tersimpan: {json_path} ({len(parts)} bagian)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
