#!/usr/bin/env python3
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
TODAY = datetime.datetime.utcnow().strftime("%Y%m%d")
NOW = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

feed = json.load(open(os.path.join(DATA, f"feed_{TODAY}.json")))
tempo = json.load(open(os.path.join(DATA, f"tempo_{TODAY}.json")))
yt = json.load(open(os.path.join(DATA, f"tempo_yt_{TODAY}.json")))

# ---- techbro ----
tweets_total = feed["total_tweets"]
from collections import Counter
tb = [t for t in feed["tweets"] if t.get("is_techbro_id")]
cnt = Counter(t["user"] for t in tb)
contributors = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
    {
        "title": "Pembaruan AI Indonesia: dari Brief Harian hingga ChatHPT",
        "summary": "Aliran kabar AI kembali padat: @ainunnajib merilis AI DAILY BRIEF 27 Agustus, @girikuncoro menyebarkan Grok Bot untuk publik, dan @ismailfahmi membeberkan 4.328 pertanyaan ChatHPT.",
        "body": [
            "@ainunnajib membuka hari dengan AI DAILY BRIEF 27 Agustus yang menyimpulkan vibe AI hari itu seperti 'tiga race sekaligus', menyiratkan laju rilis model yang saling kejar. Ringkasan harian ini jadi barometer tak resmi bagi lingkaran techbro lokal untuk menangkap arah industri.",
            "@girikuncoro meneruskan kabar bahwa Grok Bot kini tersedia untuk semua pengguna dengan langganan Grok atau Cursor standar, produk yang disebut tumbuh paling cepat dari xAI. Sementara @lucaxyzz membagikan 'good read' dan @lynxluna menyebar peringatan soal posting kontroversi air-AI yang salah pakai AI tanpa disclosur.",
            "@ismailfahmi menutup siklus ini dengan data nyata: dari 4.328 pertanyaan yang masuk ke ChatHPT selama uji coba 9 hari, terlihat pola minat pengguna Indonesia terhadap asisten bahasa lokal. Angka ini jadi bukti adopsi nyata, bukan sekadar hype, bagi ekosistem AI berbahasa Indonesia."
        ]
    },
    {
        "title": "Gamedev & Open Source: Capcom Menghajar, Ubisoft Terpeleset",
        "summary": "Obrolan industri game mendominasi timeline @lynxluna: RE Engine Capcom 'crushing 2026', kegagalan rilis Telosoft/Ubisoft, dan lelucon fork-repo dari @__r17x.",
        "body": [
            "@lynxluna mengawal narasi gamedev dengan deretan angka: RE Requiem (Feb 2026, 7 juta kopi), Monster Hunter Stories, dan Capcom yang disebutnya 'crushing 2026' lewat RE Engine. Untuk contrast, ia melempar candaan soal 'si TELOSOFT @Ubisoft lupa upload game files' dan membandingkannya dengan rilis mulus CD Projekt Red.",
            "Humor engineering juga muncul dari @__r17x yang menyoroti betapa tidak gampangnya 'nge-fork repository' ketika penolakan berubah jadi ambisi, serta 'Nix fix this?' yang jadi meme penyembuhan bagi pengguna Nix. @lucaxyzz menambah bacaan panjang soal tooling yang layak disimak.",
            "Lapisan budaya dipertegas @lynxluna lewat RT soal indie game release dan 'botching', mengingatkan bahwa kegagalan rilis raksasa seperti Ubisoft tetap jadi pelajaran berharga bagi developer independen Indonesia. Komunitas merespons dengan campuran ejekan dan solidaritas khas."
        ]
    },
    {
        "title": "Civic Tech & Bencana: Drone Emprit Pantau Demo 27 Agustus",
        "summary": "@ismailfahmi merilis fitur virality analysis Drone Emprit untuk isu Demo 27 Agustus, sementara @ArdyaDipta menyebar 'ALL EYES ON INDONESIA' soal tumpukan bencana daerah.",
        "body": [
            "@ismailfahmi membedah Isu Demo 27 Agustus 2026 lewat fitur virality analysis Drone Emprit yang melacak tagar dari waktu ke waktu dan lintas platform. Ia juga mencatat #DemoPatiDibatalkan sebagai counter-naratif yang masih berjalan, menunjukkan bagaimana alat analitik kini jadi bagian dari perang narasi sipil.",
            "@ArdyaDipta meneruskan 'ALL EYES ON INDONESIA' yang merangkum penderitaan bertumpuk: Aceh belum pulih, Padang banjir bandang, Kalimantan kebakaran, NTT gempa 7,7 SR, dan Papua terbakar. De.ret hutan Semeru juga ditutup @ismailfahmi akibat kebakaran 26 Agustus, melengkapi catatan krisis.",
            "Di sisi resmi, @susipudjiastuti menekankan pemikiran Presiden Prabowo soal standar penanganan bencana ke depan dan memuji pejabat yang turun langsung. Klaim itu langsung berbenturan dengan realitas di lapangan yang dibeberkan lingkaran civic-tech, memunculkan jurang antara narasi dan fakta."
        ]
    },
    {
        "title": "Banter Komunitas: dari Mr.X hingga RIP Legenda",
        "summary": "Sisi personal techbro tetap hangat: @lynxluna dengan kisah 'dikuntit Mr.X', @MikaelDewabrata mengenang Tim Curry & Dolly Parton, dan @__r17x penuh meme.",
        "body": [
            "@lynxluna membuka sisi manusiawi lewat curhat 'dikuntit ama Mr.X' yang bikin deg-degan dan obrolan tentang menghadapi ketakutan serta stalking yang memicu anxiety. Ia juga menyentil dinamika hijab antar-generasi, menunjukkan techbro tak cuma membahas kode.",
            "@MikaelDewabrata dan @__r17x mengisi jeda dengan kehilangan budaya: 'RiP Tim Curry' dan 'Rest in Peace, Dolly Parton' diiringi meme 'OK! LGBTM' serta 'Mom! I'm on the TV'. Interaksi ringan seperti balasan ke @ardi_tama1 menambah rasa komunitas yang akrab.",
            "@ismailfahmi menutup dengan nuansa tenang: Ranu Kumbolo di 2.400 mdpl dan keheningan sebelum pendaki datang, plus pertanyaan Tarjih Muhammadiyah soal qunut. Campuran guyonan dan refleksi ini yang membuat timeline techbro Indonesia terasa hidup dan tidak monoton."
        ]
    },
]

# ---- tempo ----
from collections import defaultdict
groups_d = defaultdict(list)
for a in tempo["articles"]:
    cat = a.get("source", "").replace("tempo:", "").title() or "Lainnya"
    if len(groups_d[cat]) >= 3:
        continue
    groups_d[cat].append({
        "title": a["title"],
        "link": a["link"],
        "source": a.get("source", "")
    })
groups = [{"category": c, "articles": arts} for c, arts in groups_d.items()]
tempo_count = sum(len(g["articles"]) for g in groups)
tempo_count = min(tempo_count, 12)

# ---- pinggir_jurang ----
pinggir = [
    {
        "title": "Bencana Bertubi-tubi, Janji Penanganan yang Belum Menyelamatkan",
        "summary": "Saat @susipudjiastuti memuji standar bencana Presiden Prabowo, Aceh, Padang, Kalimantan, NTT, dan Papua masih bergelut dengan krisis nyata yang tak selesai.",
        "body": [
            "Naratif resmi mengklaim pejabat kini langsung turun ke lapangan dan standar penanganan Presiden Prabowo akan jadi rujukan ke depan. Namun 'ALL EYES ON INDONESIA' yang diteruskan @ArdyaDipta mencatat Aceh yang belum pulih, Padang banjir bandang, Kalimantan kebakaran, NTT gempa 7,7 SR, dan Papua terbakar dalam satu rentetan.",
            "Penutupan jalur pendakian Semeru akibat kebakaran 26 Agustus, ditambah kabut asap yang memaksa PJJ di sejumlah sekolah, menunjukkan dampak beruntun yang tak cuma soal respons cepat tapi soal mitigasi jangka panjang yang tak kunjung memadai.",
            "Jurang antara pujian di atas kertas dan penderitaan di lapangan kian lebar: satu sisi merayakan prosedur, sisi lain warga masih menghirup asap dan kehilangan akses. Pertanyaan kritisnya sederhana—berapa banyak bencana lagi sebelum standar itu benar-benar terasa di akar?"
        ]
    },
    {
        "title": "Demo 27 Agustus: Perang Narasi dan Upaya Pembungkaman",
        "summary": "Drone Emprit menangkap lahirnya #DemoPatiDibatalkan sebagai counter-naratif, mengungkap bagaimana isu demo diputarbalikkan alih-alih didengarkan.",
        "body": [
            "@ismailfahmi membuka keran data: virality analysis Drone Emprit melacak #DemoPatiDibatalkan yang berjalan sebagai counter-naratif atas ajakan demo 27 Agustus. Alat analitik itu sendiri jadi saksi betapa cepatnya mesin narasi membalik arah percakapan publik.",
            "Yang mengkhawatirkan bukan demo itu sendiri, melainkan pola di mana keresahan warga direspons dengan pelabelan dan pembungkaman rather than dialog. Tagar pembatal jadi instrumen pelunak yang berisiko mengaburkan tuntutan asli di balik kerumunan kata.",
            "Di pinggir jurang, oposisi dan warga netrak mengingatkan: ketika analitik virality dipakai untuk memetakan siapa yang 'tertangkap', ruang kritis menyempit. Demo bukan sekadar kerumunan—ia sinyal gagalnya saluran resmi menampung suara sebelum asap kebakaran pun ikut mematikan sekolah."
        ]
    },
]

# ---- youtube ----
youtube = [{"title": v["title"], "channel": v["channel"], "link": v["url"]}
           for v in yt.get("videos", [])][:5]

digest = {
    "generated_at": NOW,
    "techbro": {
        "tweets_total": tweets_total,
        "contributors": contributors,
        "themes": themes,
    },
    "tempo": {
        "count": tempo_count,
        "categories": {"groups": groups},
    },
    "pinggir_jurang": {"themes": pinggir},
    "youtube": youtube,
}

out = os.path.join(DATA, f"digest_{TODAY}.json")
with open(out, "w") as f:
    json.dump(digest, f, ensure_ascii=False, indent=2)

print(f"DIGEST_WRITTEN data/digest_{TODAY}.json themes={len(themes)} tempo={tempo_count} yt={len(youtube)}")
