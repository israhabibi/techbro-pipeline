#!/usr/bin/env python3
"""
pre_collect.py - Hackathon POC: kumpulkan tweet health-misinfo Indonesia.

Strategi (robust terhadap blokir Twitter):
  1. Coba raw search/adaptive per keyword (creds @Isra_habibi)
  2. Kalau search di-blokir (body kosong / 403), FALLBACK ke home timeline
     (scan.py style) lalu filter tweet yg mengandung keyword health.
  3. Dedup by tweet_id + text-hash, simpan ke PostgreSQL (db healthmis).

Jalankan:
  source .venv/bin/activate
  python3 pre_collect.py            # default: semua keyword, max 200 tweet
  python3 pre_collect.py --max 300 --keyword "vaksin bahaya"
"""
import json, os, sys, time, datetime, hashlib, argparse, urllib.request, urllib.error, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
CREDS = os.environ.get("CREDS_FILE", os.path.join(os.path.dirname(BASE), "creds.json"))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

# ---- Health misinfo keyword (dari brief hackathon) ----
KEYWORDS = [
    "obat covid herbal sembuh",
    "vaksin bahaya microchip",
    "minyak kayu putih corona",
    "baking soda kanker",
    "dokter tidak mau kamu tahu",
    "air rebusan daun sembuhkan",
]

PG = dict(host="localhost", port=5432, dbname="healthmis",
          user="halodoc", password="halodoc123")

# ---- Twitter creds helpers ----
def load_creds():
    if not os.path.isfile(CREDS):
        raise FileNotFoundError(f"Credentials file not found: {CREDS} (set CREDS_FILE to override)")
    with open(CREDS) as f:
        return json.load(f)

def _headers(creds):
    return {
        "Authorization": f"Bearer {creds['bearer']}",
        "X-Csrf-Token": creds["ct0"],
        "Cookie": (f'auth_token={creds["auth_token"]}; ct0={creds["ct0"]}; '
                   f'twid={creds.get("twid","")}; kdt={creds.get("kdt","")}; lang=id'),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Auth-Type": "OAuth2Session",
    }

def raw_search(creds, q, count=20):
    """Return list dict {id,text,created_at,user,lang} atau [] kalau di-blokir."""
    url = ("https://x.com/i/api/2/search/adaptive.json?q=" + urllib.parse.quote(q)
           + f"&result_filter=latest&count={count}&tweet_search_mode=live&include_entities=true")
    req = urllib.request.Request(url, headers=_headers(creds))
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode(errors="replace")
        if not body.strip():
            return []  # soft-block: body kosong
        d = json.loads(body)
        tw = d.get("globalObjects", {}).get("tweets", {})
        us = d.get("globalObjects", {}).get("users", {})
        out = []
        for tid, t in tw.items():
            u = us.get(t.get("user_id_str", ""), {})
            out.append({
                "id": tid, "text": t.get("text", ""),
                "created_at": t.get("created_at"),
                "user": u.get("screen_name", ""),
                "lang": t.get("lang", ""),
            })
        return out
    except Exception as e:
        print(f"  [search warn] {q}: {e}", file=sys.stderr)
        return []

def raw_home_timeline(creds, count=40, cursor=None):
    url = (f'https://x.com/i/api/2/timeline/home.json?count={count}'
           f'&include_entities=true&latest=true')
    if cursor:
        url += f'&cursor={urllib.parse.quote(cursor)}'
    req = urllib.request.Request(url, headers=_headers(creds))
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [timeline warn] {e}", file=sys.stderr)
        return None

def collect_via_timeline(creds, keywords, pages=5):
    """Fallback: ambil home timeline, filter tweet yg mengandung keyword."""
    kset = [k.lower() for k in keywords]
    seen = {}
    cursor = None
    for i in range(pages):
        d = raw_home_timeline(creds, count=40, cursor=cursor)
        if not d:
            break
        tw = d.get("globalObjects", {}).get("tweets", {})
        us = d.get("globalObjects", {}).get("users", {})
        for tid, t in tw.items():
            txt = (t.get("text") or "").lower()
            if any(k in txt for k in kset):
                u = us.get(t.get("user_id_str", ""), {})
                seen[tid] = {
                    "id": tid, "text": t.get("text", ""),
                    "created_at": t.get("created_at"),
                    "user": u.get("screen_name", ""), "lang": t.get("lang", ""),
                }
        # cursor
        cursor = None
        for ins in d.get("timeline", {}).get("instructions", []):
            for e in (ins.get("addEntries", {}).get("entries", []) or ins.get("entries", [])):
                op = e.get("content", {}).get("operation", {})
                if op.get("cursor", {}).get("cursorType") == "Bottom":
                    cursor = op["cursor"].get("value")
        if not cursor:
            break
        time.sleep(2)
    return list(seen.values())

# ---- DB ----
def ensure_schema(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tweets (
        id TEXT PRIMARY KEY,
        text TEXT,
        created_at TIMESTAMP,
        username TEXT,
        lang TEXT,
        keyword TEXT,
        text_hash TEXT,
        collected_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        tweet_id TEXT REFERENCES tweets(id),
        reviewer TEXT,
        verdict TEXT,
        note TEXT,
        reviewed_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()

def text_hash(t):
    return hashlib.sha256((t or "").strip().lower().encode()).hexdigest()[:16]

def save(conn, tweets, keyword):
    cur = conn.cursor()
    n = 0
    for t in tweets:
        h = text_hash(t["text"])
        cur.execute("SELECT 1 FROM tweets WHERE text_hash=%s OR id=%s", (h, t["id"]))
        if cur.fetchone():
            continue  # dedup
        cur.execute(
            "INSERT INTO tweets (id,text,created_at,username,lang,keyword,text_hash) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (t["id"], t["text"], _parse_dt(t["created_at"]), t["user"], t["lang"], keyword, h))
        n += 1
    conn.commit()
    cur.close()
    return n

def _parse_dt(s):
    if not s:
        return None
    for fmt in ("%a %b %d %H:%M:%S +0000 %Y", "%Y-%m-%dT%H:%M:%S.000Z"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except Exception:
            pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--keyword", type=str, default=None)
    ap.add_argument("--timeline-only", action="store_true")
    args = ap.parse_args()

    import psycopg2
    creds = load_creds()
    conn = psycopg2.connect(**PG)
    ensure_schema(conn)

    kws = [args.keyword] if args.keyword else KEYWORDS
    total = 0
    used_search = False
    for kw in kws:
        if args.timeline_only:
            print(f"[skip search] {kw} (timeline-only mode)")
            continue
        res = raw_search(creds, kw, count=20)
        if res:
            used_search = True
            saved = save(conn, res, kw)
            total += saved
            print(f"[search] {kw}: {len(res)} raw, {saved} baru")
        if total >= args.max:
            break
        time.sleep(3)

    if not used_search and total == 0:
        print("[fallback] search di-blokir, pakai home timeline + filter keyword...")
        tl = collect_via_timeline(creds, kws, pages=6)
        saved = save(conn, tl, "timeline-filter")
        total += saved
        print(f"[timeline] {len(tl)} match, {saved} baru")

    print(f"\nTotal tweet terkumpul: {total}")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tweets")
    print("DB tweets total:", cur.fetchone()[0])
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
