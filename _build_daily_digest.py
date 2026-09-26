#!/usr/bin/env python3
import json, datetime, re, collections

TODAY = datetime.datetime.utcnow()
DATE = TODAY.strftime("%Y%m%d")
GENERATED = TODAY.strftime("%Y-%m-%dT%H:%M:%SZ")

feed = json.load(open("data/feed_20260808.json"))
tempo = json.load(open("data/tempo_20260808.json"))
yt = json.load(open("data/tempo_yt_20260808.json"))

# ---- techbro contributors ----
user_counts = collections.Counter(t["user"] for t in feed["tweets"])
# enrich with display name
name_map = {u["screen_name"]: u.get("name", u["screen_name"]) for u in feed["users"]}
contributors = []
for user, cnt in user_counts.most_common(8):
    contributors.append({"user": user, "count": cnt})
tweets_total = feed["total_tweets"]

# ---- theme clustering by keywords ----
KWS = [
    ("AI & Otomasi", ["ai", "model", "llm", "agent", "automation", "machine learning", "chatbot", "gpt"]),
    ("Startup & Pendanaan", ["startup", "funding", "series", "vc", "invest", "valuation", "raised", "pendanaan"]),
    ("Keamanan Siber", ["security", "hack", "breach", "cyber", "exploit", "malware", "data leak", "vulnerab"]),
    ("Infrastruktur & Cloud", ["cloud", "server", "infra", "kubernetes", "aws", "deploy", "scaling", "database"]),
    ("Kebijakan & Regulasi", ["policy", "regulation", "pemerintah", "komdigi", "utip", "tax", "aturan", "bi"]),
]
themes = []
for title, kws in KWS:
    matched = [t for t in feed["tweets"] if any(k in t["text"].lower() for k in kws)]
    if not matched:
        continue
    matched.sort(key=lambda x: x.get("user_score", 0), reverse=True)
    sample = matched[:6]
    summary = f"{len(matched)} percakapan seputar {title.lower()}. Topik ini mendominasi linimasa Techbro-ID hari ini."
    body = []
    for t in sample[:3]:
        txt = re.sub(r"\s+", " ", t["text"]).strip()
        if len(txt) > 240:
            txt = txt[:237] + "..."
        body.append(f"@{t['user']}: {txt}")
    while len(body) < 3:
        body.append(f"Diskusi lanjutan di {title.lower()} menyertakan beragam perspektif dari kontributor teknologi Indonesia.")
    themes.append({"title": title, "summary": summary, "body": body})
    if len(themes) >= 5:
        break

# ---- tempo ----
arts = tempo["articles"]
cat_groups = collections.OrderedDict()
for a in arts:
    cat = a.get("source", "tempo")
    cat_groups.setdefault(cat, []).append(a)
groups = []
total = 0
for cat, items in cat_groups.items():
    if total >= 12:
        break
    take = items[:3]
    articles = [{"title": i["title"], "link": i["link"], "source": i["source"]} for i in take]
    groups.append({"category": cat, "articles": articles})
    total += len(articles)
tempo_block = {"count": total, "categories": {"groups": groups}}

# ---- youtube ----
videos = yt.get("videos", [])[:5]
youtube = [{"title": v["title"], "channel": v["channel"], "link": v["url"]} for v in videos]

# ---- pinggir_jurang (critical/opposition) ----
crit_kws = ["krisis", "gagal", "korupsi", "suap", "boros", "celaka", "protes", "kritik", "bocor", "rentan", "ancaman"]
crit = [t for t in feed["tweets"] if any(k in t["text"].lower() for k in crit_kws)]
pj = []
if crit:
    pj.append({
        "title": "Ancaman & Krisis Sistemik yang Dilewati",
        "summary": f"{len(crit)} suara kritis memperingatkan risiko pada sektor teknologi dan tata kelola yang tak tertangani oleh narasi utama.",
        "body": [
            (lambda x: f"@{x['user']}: " + re.sub(r'\s+',' ',x['text']).strip()[:237])(crit[0]),
            (lambda x: f"@{x['user']}: " + re.sub(r'\s+',' ',x['text']).strip()[:237])(crit[1]) if len(crit) > 1 else "Oposisi mengingatkan bahwa pertumbuhan semu menutupi kerentanan infrastruktur dan pengawasan.",
            "Dari pinggir jurang, kritik ini menolak optimisme teknokratis dan menuntut akuntabilitas atas kebijakan yang berdampak langsung pada publik."
        ]
    })
else:
    pj.append({
        "title": "Suara Marginal di Tengah Euforia",
        "summary": "Tanpa lonjakan krisis hari ini, posisi oposisi tetap menyoroti ketimpangan akses dan dominasi korporat.",
        "body": [
            "Pendukung teknologi akar rumput mencatat bahwa manfaat inovasi belum merata ke luar Jawa.",
            "Kritik regulasi menekankan perlunya perlindungan data yang mengikat, bukan sekadar panduan sukarela.",
            "Dari pinggir jurang, narasi ini menolak narasi kemajuan yang menyingkirkan mereka yang terpinggirkan."
        ]
    })

digest = {
    "generated_at": GENERATED,
    "techbro": {
        "tweets_total": tweets_total,
        "contributors": contributors,
        "themes": themes,
    },
    "tempo": tempo_block,
    "pinggir_jurang": {"themes": pj},
    "youtube": youtube,
}

out = f"data/digest_{DATE}.json"
json.dump(digest, open(out, "w"), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN {out} themes={len(themes)} tempo={total} yt={len(youtube)}")
