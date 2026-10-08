#!/usr/bin/env python3
"""
X home-timeline scanner -> kategorisasi techbro Indonesia.
Menulis hasil ke data/feed_YYYYMMDD.json
"""

import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from techbro_pipeline.config import Settings, day_stamp, write_json

SETTINGS = Settings.from_env()
CREDS = str(SETTINGS.credentials_file)
DATA = str(SETTINGS.data_dir)

# ---- Reference techbro Indonesia (seed dari user) ----
REF_HANDLES = {
    "ibharimarif",
    "anvie",
    "lynxluna",
    "ainunnajib",
    "ardyadipta",
    "gwirjawan",
    "lucaxyzz",
    "__r17x",
    "crackalamoo",
    "tetsuo_cpp",
    "girikuncoro",
}
# kata kunci bahasa Indonesia / tech di bio
ID_WORDS = [
    "indonesia",
    "jakarta",
    "bandung",
    "yogyakarta",
    "surabaya",
    "jogja",
    "bekasi",
    "depok",
    "medan",
    "semarang",
    "bali",
    "engineer",
    "developer",
    "founder",
    "co-founder",
    "cto",
    "programmer",
    "software",
    "ai",
    "ml",
    "data",
    "startup",
    "teknologi",
    "pemrograman",
    "backend",
    "frontend",
    "devops",
    "machine learning",
    "rekayasa",
    "koding",
    "ngoding",
]
TECH_WORDS = [
    "engineer",
    "developer",
    "founder",
    "cto",
    "programmer",
    "software",
    "ai",
    "ml",
    "data",
    "startup",
    "tech",
    "code",
    "coding",
    "devops",
    "backend",
    "frontend",
    "machine learning",
    "open source",
    "opensource",
    "python",
    "rust",
    "golang",
    "infra",
    "cloud",
    "security",
    "hacker",
]

# Kata/istilah yang cukup kuat untuk mengenali tweet teknis meski profilnya minim.
TECH_TWEET_TERMS = [
    "observability",
    "vibe coding",
    "software engineering",
    "software",
    "programming",
    "programmer",
    "developer",
    "engineering",
    "engineer",
    "backend",
    "frontend",
    "fullstack",
    "devops",
    "api",
    "sdk",
    "database",
    "postgres",
    "redis",
    "kubernetes",
    "docker",
    "linux",
    "python",
    "javascript",
    "typescript",
    "golang",
    "rust",
    "compiler",
    "open source",
    "github",
    "machine learning",
    "deep learning",
    "neural network",
    "llm",
    "gpu",
    "inference",
    "fine-tuning",
    "fine tuning",
    "cloud",
    "infrastructure",
    "cybersecurity",
    "security vulnerability",
    "coding",
    "code review",
    "code",
    "ngoding",
    "koding",
    "pull request",
    "ci/cd",
    "deployment",
    "deploy",
    "microservice",
    "distributed systems",
    "web development",
    "database schema",
    "ai tools",
    "ai video",
    "ai agent",
    "agent builds",
    "opus",
    "ultracode",
    "elevenlabs",
    "hyperframes",
    "chatgpt",
    "claude",
    "codex",
    "gemini",
    "video generation",
    "prompt engineering",
]


def load_creds():
    if not os.path.isfile(CREDS):
        raise FileNotFoundError(f"Credentials file not found: {CREDS} (set CREDS_FILE to override)")
    with open(CREDS) as f:
        credentials = json.load(f)
    if not isinstance(credentials, dict) or any(
        not isinstance(credentials.get(key), str) or not credentials[key].strip()
        for key in ("bearer", "auth_token", "ct0")
    ):
        raise ValueError("Credentials must contain nonempty bearer, auth_token, and ct0 strings")
    return credentials


def fetch_timeline(creds, count=40, cursor=None):
    AUTH = creds["bearer"]
    CK = (
        f"auth_token={creds['auth_token']}; "
        f"ct0={creds['ct0']}; twid={creds.get('twid', '')}; "
        f"kdt={creds.get('kdt', '')}; lang=en"
    )
    url = (
        f"https://x.com/i/api/2/timeline/home.json?count={count}"
        f"&candidate_source=algorithmic&include_entities=true&latest=true"
    )
    if cursor:
        url += f"&cursor={urllib.parse.quote(cursor)}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {AUTH}",
            "X-Csrf-Token": creds["ct0"],
            "Cookie": CK,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "X-Twitter-Active-User": "yes",
            "X-Twitter-Auth-Type": "OAuth2Session",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def classify_user(u):
    """Return (is_techbro_id, reasons[]). Strict: must be clearly tech/indo."""
    sn = (u.get("screen_name") or "").lower()
    name = (u.get("name") or "").lower()
    desc = (u.get("description") or "").lower()
    loc = (u.get("location") or "").lower()
    reasons = []
    score = 0
    if sn in REF_HANDLES:
        reasons.append("reference_handle")
        score += 3
    # location indonesia (strong signal)
    loc_hit = None
    for w in [
        "indonesia",
        "jakarta",
        "bandung",
        "yogyakarta",
        "jogja",
        "surabaya",
        "bali",
        "medan",
        "bekasi",
        "depok",
        "indonesia.",
    ]:
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", loc):
            loc_hit = w
            reasons.append(f"loc:{w}")
            score += 2
            break
    # specific tech keywords (strong, not just "ai")
    TECH_SPECIFIC = [
        "engineer",
        "developer",
        "cto",
        "programmer",
        "software",
        "startup",
        "tech",
        "coding",
        "devops",
        "backend",
        "frontend",
        "machine learning",
        "open source",
        "opensource",
        "python",
        "rust",
        "golang",
        "infra",
        "cloud",
        "security",
        "hacker",
        "ngoding",
        "koding",
        "rekayasa",
        "pemrograman",
        "teknologi",
        "data",
    ]
    tech_hit = None
    blob = f"{name} {desc}"
    for w in TECH_SPECIFIC:
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", blob):
            tech_hit = w
            reasons.append(f"tech:{w}")
            score += 2
            break
    # weak signal: lone "ai" only counts if combined with loc indonesia
    if not tech_hit and re.search(r"(?<!\w)ai(?!\w)", blob) and loc_hit:
        reasons.append("ai+loc")
        score += 1
    # A user is techbro-ID if: reference, OR (indo location AND tech keyword)
    # AI + an Indonesian location is an intentional fallback signal (e.g.
    # builders whose bio says "AI tools" but not developer/software).
    ai_loc_hit = "ai+loc" in reasons
    is_tech = bool(
        bool(reasons)
        and (score >= 3)
        and (sn in REF_HANDLES or (loc_hit and tech_hit) or ai_loc_hit or (tech_hit and score >= 4))
    )
    return is_tech, reasons, score


def detect_tech_tweet(text):
    """Return the first strong technical signal in a tweet, if present."""
    text = (text or "").lower()
    for term in TECH_TWEET_TERMS:
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        if re.search(pattern, text):
            return term
    return None


def main(pages=3):
    if not 1 <= pages <= 100:
        raise ValueError("pages must be between 1 and 100")
    creds = load_creds()
    all_tweets = {}
    all_users = {}
    cursor = None
    for i in range(pages):
        try:
            d = fetch_timeline(creds, count=40, cursor=cursor)
        except Exception as e:
            print(f"[warn] page {i} failed: {e}", file=sys.stderr)
            return 1
        if not isinstance(d, dict) or not isinstance(d.get("globalObjects"), dict):
            print("[error] X returned an unsupported timeline response", file=sys.stderr)
            return 1
        tw = d.get("globalObjects", {}).get("tweets", {})
        us = d.get("globalObjects", {}).get("users", {})
        all_tweets.update(tw)
        all_users.update(us)
        # find cursor
        instr = d.get("timeline", {}).get("instructions", [])
        cursor = None
        for ins in instr:
            ents = ins.get("addEntries", {}).get("entries", []) or ins.get("entries", [])
            for e in ents:
                if (
                    e.get("content", {}).get("operation", {}).get("cursor", {}).get("cursorType")
                    == "Bottom"
                ):
                    cursor = e["content"]["operation"]["cursor"].get("value")
        print(f"[page {i}] tweets={len(tw)} users={len(us)} cursor={bool(cursor)}")
        if not cursor:
            break
        time.sleep(2)
    # Tweet content can identify technical posts, but it cannot establish that
    # an account belongs to Indonesia. Keep those signals separate.
    tweet_signals = {}
    for t in all_tweets.values():
        uid = t.get("user_id_str") or (t.get("user") or {}).get("id_str")
        signal = detect_tech_tweet(t.get("text"))
        if uid and signal:
            tweet_signals.setdefault(uid, []).append(signal)

    # classify users
    classified = {}
    for uid, u in all_users.items():
        is_tb, reasons, score = classify_user(u)
        signals = list(dict.fromkeys(tweet_signals.get(uid, [])))[:3]
        reasons.extend(f"tweet:{signal}" for signal in signals)
        classified[uid] = {
            "screen_name": u.get("screen_name"),
            "name": u.get("name"),
            "location": u.get("location"),
            "followers": u.get("followers_count"),
            # X only supplies this relationship flag for some timeline accounts.
            "following": u.get("following") if isinstance(u.get("following"), bool) else None,
            "description": u.get("description"),
            "is_techbro_id": is_tb,
            "score": score,
            "reasons": reasons,
        }
    # attach tweets with classification
    out_tweets = []
    for tid, t in all_tweets.items():
        uid = t.get("user_id_str") or (t.get("user") or {}).get("id_str")
        cu = classified.get(uid, {})
        out_tweets.append(
            {
                "id": tid,
                "text": t.get("text"),
                "created_at": t.get("created_at"),
                "user": cu.get("screen_name"),
                "is_techbro_id": cu.get("is_techbro_id", False),
                "following": cu.get("following"),
                "user_score": cu.get("score", 0),
                "user_reasons": cu.get("reasons", []),
                "is_tech_tweet": bool(detect_tech_tweet(t.get("text"))),
                "tweet_tech_signal": detect_tech_tweet(t.get("text")),
            }
        )
    out_tweets.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    tech_tweets = [x for x in out_tweets if x["is_techbro_id"]]
    out = {
        "scanned_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "pages": pages,
        "total_tweets": len(out_tweets),
        "total_users": len(classified),
        "techbro_tweets": len(tech_tweets),
        "users": list(classified.values()),
        "tweets": out_tweets,
    }
    fname = os.path.join(DATA, "feed", f"feed_{day_stamp()}.json")
    write_json(fname, out)
    print(f"\nSaved -> {fname}")
    print(
        f"Total tweets: {len(out_tweets)} | Users: {len(classified)} | Techbro-ID tweets: {len(tech_tweets)}"
    )
    print("\n--- Techbro Indonesia users found ---")
    for u in sorted(classified.values(), key=lambda x: -x["score"]):
        if u["is_techbro_id"]:
            print(f"  @{u['screen_name']:18} score={u['score']} reasons={u['reasons']}")


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    raise SystemExit(main(pages))
