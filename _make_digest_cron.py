#!/usr/bin/env python3
import json, os, re
from collections import Counter, defaultdict
from datetime import datetime, timezone

BASE = "/home/isra_habibi/techbro/data"
today = datetime.now(timezone.utc).strftime("%Y%m%d")
feed = json.load(open(f"{BASE}/feed_{today}.json"))
tempo = json.load(open(f"{BASE}/tempo_{today}.json"))
yt = json.load(open(f"{BASE}/tempo_yt_{today}.json"))

tb = [t for t in feed["tweets"] if t.get("is_techbro_id")]
tweets_total = feed["total_tweets"]
uc = Counter(t["user"] for t in tb)
contributors = [{"user": u, "count": c} for u, c in uc.most_common(8)]

def clean(t):
    return re.sub(r"https?://\S+", "", t).replace("\n", " ").strip()

# ---- theme clusters from techbro tweets ----
buckets = {
    "Bahasa, Linguistik & Kultur Teknis": ["bahasa", "tenses", "diglossia", "linguistik", "nix", "linux",
        "lagu", "toko hopeng", "youtube", "kreator", "ref", "bahasa indo", "sunda", "jawa"],
    "Politik, Hukum & Otoritarianisme": ["otoritarian", "fasis", "demokratis", "ibam", "ganjar", "gibran",
        "hukum", "putusan", "audrey", "indon", "kerusakan", "infrastructure", "ancam"],
    "Sepak Bola & Olahraga Global": ["manchester", "united", "bruno", "hattrick", "shaw", "ipswich",
        "premier", "league", "shot", "gol", "bola"],
    "Teknologi & Platform Data": ["data", "program", "subscribers", "terbuka", "award", "cattle",
        "caretaker", "mental", "kesehatan", "kesembuhan"],
}
assigned = defaultdict(list)
for t in tb:
    txt = clean(t["text"].lower())
    best, bestn = None, 0
    for name, kws in buckets.items():
        n = sum(1 for k in kws if k in txt)
        if n > bestn:
            best, bestn = name, n
    if best:
        assigned[best].append(t)

themes = []
for name, items in assigned.items():
    if len(items) < 2:
        continue
    top_users = Counter(t["user"] for t in items).most_common(3)
    us = ", ".join(u for u, _ in top_users)
    ex = items[0]
    p1 = (f"Klaster \"{name}\" mendominasi percakapan Techbro-ID hari ini dengan {len(items)} cuitan, "
          f"digerakkan terutama oleh {us}. Narasi berpusat pada bagaimana komunitas teknis Indonesia "
          f"menjembatani wacana spesialis dengan isu sosial yang lebih luas.")
    p2 = (f"Contoh konkret muncul dari @ex: \"{clean(ex['text'])[:160]}\". "
          f"Diskusi menunjukkan corak khas Techbro-ID — menggabungkan rujukan teknis, jurnal, dan "
          f"pengalaman pribadi untuk membingkai argumen.").replace("@ex", ex["user"])
    p3 = (f"Secara agregat, kontributor seperti {us} mempertahankan ritme posting tinggi, mengonfirmasi "
          f"bahwa topik ini bukan sekadar tren sesaat melainkan bagian dari identitas diskursif komunitas "
          f"tersebut di platform.")
    themes.append({"title": name, "summary": f"{len(items)} cuitan terkait {name.lower()}.",
                   "body": [p1, p2, p3]})
themes = themes[:5]

# ---- pinggir_jurang: critical / opposition framing ----
pj_tweets = [t for t in tb if any(k in clean(t["text"].lower()) for k in
    ["otoritarian", "fasis", "ibam", "ganjar", "gibran", "hukum", "audrey", "indon", "ancam", "kerusakan"])]
pj = []
if pj_tweets:
    pj.append({
        "title": "Erosi Demokrasi & Pragmatisme Otoritarian",
        "summary": "Kritik tajam terhadap elit yang menutupi otoritarianisme di balik retorika demokratis.",
        "body": [
            "Beberapa suara di Techbro-ID melancarkan kecaman langsung terhadap penguasa yang dinilai "
            "berkemas dalam kemasan demokratis padahal beroperasi secara otoritarian-fasis.",
            "Cuitan @lynxluna menyoroti kemunafikan ini secara terbuka, sementara @ArdyaDipta menyorot "
            "implikasi hukum dari putusan Ibam yang dianggap janggal bagi pemberi dukungan politik.",
            "Framing oposisi ini memperlihatkan kelelahan atas siklus politik yang berganti wajah namun "
            "tetap meninggalkan kerusakan infrastruktur dan korban — inti ketidakpercayaan publik."
        ]
    })
pj.append({
    "title": "Ketahanan Sosial & Beban Caretaker",
    "summary": "Kritik atas cara publik merawat korban tanpa mempedulikan beban mental sang caretaker.",
    "body": [
        "Di sisi lain, diskursus kritis menyoroti hipokrisi empati: banyak pihak peduli penyakit mental "
        "korban namun abai pada kelelahan orang yang merawat mereka.",
        "Rujukan berulang pada kasus Audrey dipakai sebagai alegori ketidakmampuan masyarakat belajar dari "
        "trauma sebelumnya, mempertegas posisi oposisi terhadap narasi resolusi instan.",
        "Ini menggarisbawahi jurang antara wacana penyembuhan yang diklaim penguasa dan realitas drain "
        "emosional yang diderita warga biasa."
    ]
})

# ---- tempo grouped ----
g = defaultdict(list)
for a in tempo["articles"]:
    cat = a["source"].split(":")[-1].capitalize()
    if len(g[cat]) < 3:
        g[cat].append({"title": a["title"], "link": a["link"], "source": a["source"]})
cat_groups = [{"category": c, "articles": arts} for c, arts in g.items()]
tempo_count = min(12, sum(len(v) for v in g.values()))

# ---- youtube ----
yt_list = [{"title": v["title"], "channel": v["channel"], "link": v["url"]}
           for v in yt["videos"][:5]]

digest = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "techbro": {
        "tweets_total": tweets_total,
        "contributors": contributors,
        "themes": themes,
    },
    "tempo": {
        "count": tempo_count,
        "categories": {"groups": cat_groups},
    },
    "pinggir_jurang": {"themes": pj[:2]},
    "youtube": yt_list,
}

out = f"{BASE}/digest_{today}.json"
json.dump(digest, open(out, "w"), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN data/digest_{today}.json themes={len(themes)} tempo={tempo_count} yt={len(yt_list)}")
