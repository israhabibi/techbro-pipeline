#!/usr/bin/env python3
"""Extract relevant data from today's JSON files for digest generation."""
import json, os, datetime

today = datetime.datetime.utcnow().strftime("%Y%m%d")
base = "/home/isra_habibi/techbro/data"

def load(name):
    p = os.path.join(base, f"{name}_{today}.json")
    if not os.path.exists(p):
        files = sorted([f for f in os.listdir(base) if f.startswith(name+"_") and f.endswith(".json")])
        if files:
            p = os.path.join(base, files[-1])
    with open(p) as f:
        return json.load(f)

# === FEED ===
feed = load("feed")
print("="*80)
print("FEED: total_tweets=%d, techbro_tweets=%d, users=%d" % (
    feed.get("total_tweets"), feed.get("techbro_tweets"), feed.get("total_users")))

# Build user lookup
users = {u["screen_name"]: u for u in feed.get("users", [])}
techbro_users = {u["screen_name"]: u for u in feed.get("users", []) if u.get("is_techbro_id") is True or u.get("is_techbro_id") == "data"}

print("\nTECHBRO USERS (is_techbro_id truthy):")
for sn, u in sorted(techbro_users.items()):
    print(f"  @{sn}  followers={u.get('followers')}  desc={u.get('description','')[:80]}")

# Check tweet structure
all_tweets = feed.get("tweets", [])
if all_tweets:
    print("\nSample tweet keys:", list(all_tweets[0].keys()))
    print("Sample tweet user field type:", type(all_tweets[0].get("user")))
    if isinstance(all_tweets[0].get("user"), dict):
        print("Sample tweet user keys:", list(all_tweets[0]["user"].keys()))
    else:
        print("Sample tweet user value:", all_tweets[0].get("user"))

# Extract techbro tweets
techbro_tweets = []
for t in all_tweets:
    u = t.get("user", {})
    if isinstance(u, dict):
        sn = u.get("screen_name", "")
    else:
        sn = u
    if sn in techbro_users:
        techbro_tweets.append(t)

print(f"\nTECHBRO TWEETS: {len(techbro_tweets)}")
for t in techbro_tweets:
    u = t.get("user", {})
    sn = u.get("screen_name","") if isinstance(u, dict) else u
    text = t.get("text", "")
    is_thread = "🧵" in text or any(f"{i}/{i+1}" in text for i in range(1,20))
    print(f"\n--- @{sn} | {t.get('created_at','?')} | thread={is_thread}")
    print(f"  {text[:500]}")

# Prabowo mentions in ALL tweets
print("\n" + "="*80)
print("PRABOWO MENTIONS (all tweets):")
prab_tweets = []
for t in all_tweets:
    text = t.get("text", "")
    if "prabowo" in text.lower():
        u = t.get("user", {})
        sn = u.get("screen_name","") if isinstance(u, dict) else u
        prab_tweets.append((sn, t))
        print(f"\n--- @{sn} | {t.get('created_at','?')}")
        print(f"  {text[:400]}")
print(f"\nTotal Prabowo mentions: {len(prab_tweets)}")

# === TEMPO ===
print("\n" + "="*80)
print("TEMPO:")
tempo = load("tempo")
articles = tempo.get("articles", [])
print(f"Total articles: {len(articles)}")
cats = {}
for a in articles:
    src = a.get("source", "")
    cats.setdefault(src, []).append(a)
for cat, arts in sorted(cats.items()):
    print(f"\n[{cat}] ({len(arts)} articles):")
    for a in arts[:10]:
        print(f"  - {a.get('title','')[:90]}")

# === TEMPO_YT ===
print("\n" + "="*80)
print("TEMPO_YT:")
yt = load("tempo_yt")
videos = yt.get("videos", [])
print(f"Videos: {len(videos)}")
for v in videos:
    print(f"  - {v.get('title','')} | {v.get('url','')}")

# === NEWS_MONITOR ===
print("\n" + "="*80)
print("NEWS_MONITOR:")
nm = load("news_monitor")
for topic in nm.get("topics", []):
    print(f"\nTopic: {topic.get('topic')} | matches={topic.get('matches')}")
    for a in topic.get("articles", [])[:5]:
        print(f"  [{a.get('source','')}] {a.get('title','')[:90]}")
        print(f"    link: {a.get('link','')}")
