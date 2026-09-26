#!/usr/bin/env python3
"""
X home-timeline scanner -> kategorisasi techbro Indonesia.
Menulis hasil ke data/feed_YYYYMMDD.json
"""
import json, os, sys, time, datetime, urllib.request, urllib.error, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(BASE, "creds.json")
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

# ---- Reference techbro Indonesia (seed dari user) ----
REF_HANDLES = {
    "ibharimarif", "anvie", "lynxluna", "ainunnajib",
    "ardyadipta", "gwirjawan", "lucaxyzz", "__r17x", "crackalamoo",
    "tetsuo_cpp", "girikuncoro",
}
# kata kunci bahasa Indonesia / tech di bio
ID_WORDS = ["indonesia", "jakarta", "bandung", "yogyakarta", "surabaya",
             "jogja", "bekasi", "depok", "medan", "semarang", "bali",
             "engineer", "developer", "founder", "co-founder", "cto",
             "programmer", "software", "ai", "ml", "data", "startup",
             "teknologi", "pemrograman", "backend", "frontend", "devops",
             "machine learning", "rekayasa", "koding", "ngoding"]
TECH_WORDS = ["engineer", "developer", "founder", "cto", "programmer",
               "software", "ai", "ml", "data", "startup", "tech",
               "code", "coding", "devops", "backend", "frontend",
               "machine learning", "open source", "opensource", "python",
               "rust", "golang", "infra", "cloud", "security", "hacker"]

def load_creds():
    with open(CREDS) as f:
        return json.load(f)

def fetch_timeline(creds, count=40, cursor=None):
    AUTH = creds["bearer"]
    CK = (f'auth_token={creds["auth_token"]}; '
          f'ct0={creds["ct0"]}; twid={creds.get("twid","")}; '
          f'kdt={creds.get("kdt","")}; lang=en')
    url = (f'https://x.com/i/api/2/timeline/home.json?count={count}'
           f'&candidate_source=algorithmic&include_entities=true&latest=true')
    if cursor:
        url += f'&cursor={urllib.parse.quote(cursor)}'
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {AUTH}",
        "X-Csrf-Token": creds["ct0"],
        "Cookie": CK,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Auth-Type": "OAuth2Session",
    })
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
        reasons.append("reference_handle"); score += 3
    # location indonesia (strong signal)
    loc_hit = None
    for w in ["indonesia", "jakarta", "bandung", "yogyakarta", "jogja",
               "surabaya", "bali", "medan", "bekasi", "depok", "indonesia."]:
        if w in loc:
            loc_hit = w; reasons.append(f"loc:{w}"); score += 2; break
    # specific tech keywords (strong, not just "ai")
    TECH_SPECIFIC = ["engineer", "developer", "founder", "co-founder", "cto",
                     "programmer", "software", "startup", "tech", "coding",
                     "devops", "backend", "frontend", "machine learning",
                     "open source", "opensource", "python", "rust", "golang",
                     "infra", "cloud", "security", "hacker", "ngoding",
                     "koding", "rekayasa", "pemrograman", "teknologi", "data"]
    tech_hit = None
    blob = f"{name} {desc}"
    for w in TECH_SPECIFIC:
        if w in blob:
            tech_hit = w; reasons.append(f"tech:{w}"); score += 2; break
    # weak signal: lone "ai" only counts if combined with loc indonesia
    if not tech_hit and "ai" in blob and loc_hit:
        reasons.append("ai+loc"); score += 1
    # A user is techbro-ID if: reference, OR (indo location AND tech keyword)
    is_tech = bool(reasons) and (score >= 3) and (
        sn in REF_HANDLES or (loc_hit and tech_hit) or (tech_hit and score >= 4)
    )
    return is_tech, reasons, score

def main(pages=3):
    creds = load_creds()
    all_tweets = {}
    all_users = {}
    cursor = None
    for i in range(pages):
        try:
            d = fetch_timeline(creds, count=40, cursor=cursor)
        except Exception as e:
            print(f"[warn] page {i} failed: {e}", file=sys.stderr)
            break
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
                if e.get("content", {}).get("operation", {}).get("cursor", {}).get("cursorType") == "Bottom":
                    cursor = e["content"]["operation"]["cursor"].get("value")
        print(f"[page {i}] tweets={len(tw)} users={len(us)} cursor={bool(cursor)}")
        if not cursor:
            break
        time.sleep(2)
    # classify users
    classified = {}
    for uid, u in all_users.items():
        is_tb, reasons, score = classify_user(u)
        classified[uid] = {
            "screen_name": u.get("screen_name"),
            "name": u.get("name"),
            "location": u.get("location"),
            "followers": u.get("followers_count"),
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
        out_tweets.append({
            "id": tid,
            "text": t.get("text"),
            "created_at": t.get("created_at"),
            "user": cu.get("screen_name"),
            "is_techbro_id": cu.get("is_techbro_id", False),
            "user_score": cu.get("score", 0),
            "user_reasons": cu.get("reasons", []),
        })
    out_tweets.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    tech_tweets = [x for x in out_tweets if x["is_techbro_id"]]
    out = {
        "scanned_at": datetime.datetime.utcnow().isoformat() + "Z",
        "pages": pages,
        "total_tweets": len(out_tweets),
        "total_users": len(classified),
        "techbro_tweets": len(tech_tweets),
        "users": list(classified.values()),
        "tweets": out_tweets,
    }
    fname = os.path.join(DATA, "feed_" + datetime.datetime.utcnow().strftime("%Y%m%d") + ".json")
    with open(fname, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nSaved -> {fname}")
    print(f"Total tweets: {len(out_tweets)} | Users: {len(classified)} | Techbro-ID tweets: {len(tech_tweets)}")
    print("\n--- Techbro Indonesia users found ---")
    for u in sorted(classified.values(), key=lambda x: -x["score"]):
        if u["is_techbro_id"]:
            print(f"  @{u['screen_name']:18} score={u['score']} reasons={u['reasons']}")

if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    main(pages)
