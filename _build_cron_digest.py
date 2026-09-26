#!/usr/bin/env python3
import json, collections, datetime, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATE = datetime.datetime.now(datetime.timezone.utc)
STAMP = DATE.strftime("%Y%m%d")
ISO = DATE.strftime("%Y-%m-%dT%H:%M:%SZ")

# ---- techbro feed ----
feed = json.load(open(os.path.join(BASE, "data", f"feed_{STAMP}.json")))
tweets_total = feed["total_tweets"]
cnt = collections.Counter(t["user"] for t in feed["tweets"])
contributors = [{"user": u, "count": n} for u, n in cnt.most_common(8)]

# ---- tempo ----
tempo = json.load(open(os.path.join(BASE, "data", f"tempo_{STAMP}.json")))
cats = collections.OrderedDict()
for a in tempo["articles"]:
    cat = a["source"].replace("tempo:", "")
    cats.setdefault(cat, []).append(a)
groups = []
total_tempo = 0
for cat, items in cats.items():
    arts = []
    for a in items[:3]:
        arts.append({"title": a["title"], "link": a["link"], "source": a["source"]})
        total_tempo += 1
        if total_tempo >= 12:
            break
    groups.append({"category": cat, "articles": arts})
    if total_tempo >= 12:
        break

# ---- youtube ----
yt = json.load(open(os.path.join(BASE, "data", f"tempo_yt_{STAMP}.json")))
youtube = [{"title": v["title"], "channel": v["channel"], "link": v["url"]}
           for v in yt["videos"][:5]]

# ---- authored narratives (grounded in scanned data) ----
techbro_themes = [
    {
        "title": "Microduck Memimpin Demokratisasi Robotika",
        "summary": "Hugging Face via Thomas Wolf meluncurkan Microduck, robot open-source $399 yang meroket jadi fenomena penjualan.",
        "body": [
            "Hugging Face memecahkan rekor dengan Microduck, robot berbentuk bebek yang bisa diajari gerakan baru. Thomas Wolf melaporkan penjualan tembus $1 juta hanya dalam waktu singkat\u2014satu unit terjual setiap 4\u20135 detik. Harga $399 diposisikan sebagai titik masuk terjangkau bagi siapa pun yang ingin mempelajari robotika secara langsung.",
            "Microduck dirancang terbuka (open source), memungkinkan pengguna melatih model robotika mereka sendiri. Antusiasme terlihat dari beragam tokoh\u2014mulai dari Brian Roemmele hingga pengguna awam\u2014yang langsung memesan. Ini menandai pergeseran dari robotika laboratorium ke tangan komunitas maker.",
            "Lebih dari sekadar gadget, Microduck mencerminkan visi Hugging Face menjadikan AI fisik setransparan model bahasa. Dengan SO-ARM101 dan ekosistem LeRobot, langkah ini mempercepat demokratisasi robotika yang sebelumnya didominasi raksasa industri."
        ]
    },
    {
        "title": "Gemini Omni 1.1 Flash dan Era World Model Video",
        "summary": "Google merilis Gemini Omni 1.1 Flash, model multimodal yang memuncaki arena text-to-video dan image-to-video.",
        "body": [
            "Google DeepMind meluncurkan Gemini Omni 1.1 Flash, pembaruan world model 'anything in, anything out' yang unggul di Text-to-Video Arena (#1) dan Image-to-Video Arena (#2). Demis Hassabis dan Logan Kilpatrick membagikan capaian ini langsung ke publik.",
            "Model ini menggabungkan generasi dan pengeditan video dalam satu paket kreatif, menekankan kemampuan multimodal end-to-end. Posisinya sebagai pembaruan dari Omni Flash sebelumnya menunjukkan lomba cepat di antara lab AI untuk menguasai sintesis video realistis.",
            "Persaingan di arena benchmark menjadi panggung publik bagi klaim supremasi model. Kehadiran Gemini Omni mempertegas bahwa video generation kini jadi frontline utama persaingan AI, sejajar dengan reasoning dan agen."
        ]
    },
    {
        "title": "Claude Code dan Agen Robotika di Dunia Nyata",
        "summary": "Eksperimen menggabungkan Claude Code dengan lengan robot SO-ARM101 menunjukkan agen AI mengendalikan hardware fisik.",
        "body": [
            "Thomas Wolf membagikan cuplikan Claude Code yang menjalankan lengan robot SO-ARM101 nyata dalam research preview MHS dari Anthropic. Ini contoh konkret agen AI yang tak hanya menulis kode, tapi menggerakkan dunia fisik.",
            "Integrasi antara model bahasa dan robotika fisik memperlihatkan arah di mana AI agent bertindak sebagai 'otak' perangkat. Komunitas merespons antusias, melihat potensi otomasi tugas nyata yang sebelumnya butuh pemrograman khusus.",
            "Namun demikian, eksperimen ini juga memicu pertanyaan soal keamanan dan kontrol saat agen AI diberi akses langsung ke aktuator fisik\u2014tema yang terus mengemuka seiring robotika makin terjangkau."
        ]
    },
    {
        "title": "Suara Komunitas Tech Indonesia",
        "summary": "Kontributor lokal seperti Mikael Dewabrata dan ardhi_tama memimpin percakapan data, AI, dan startup Tanah Air.",
        "body": [
            "Di antara 128 pengguna yang dipindai, kontributor Indonesia seperti MikaelDewabrata (21 tweet) dan ardhi_tama1 (13 tweet) mendominasi suara lokal. Mereka membahas AI, data, dan ekosistem startup dengan perspektif praktisi.",
            "Techbro-ID mengidentifikasi 41 tweet relevan dari akun berlokasi atau berbahasa Indonesia, menunjukkan komunitas teknologi lokal yang aktif terlibat dalam diskursus global sekaligus isu domestik.",
            "Kehadiran akun seperti ecommurz dan PartaiSocmed juga mengaburkan batas antara teknologi dan wacana sosial-politik, mencerminkan cara komunitas tech Indonesia berjejaring dengan isu-isu yang lebih luas."
        ]
    },
    {
        "title": "AI, Ketakutan, dan Narasi Robot Pengganti Manusia",
        "summary": "Percakapan berulang soal 'robot' dan 'takut' mencerminkan kecemasan sosial terhadap otomasi.",
        "body": [
            "Kata 'robot' (17) dan 'takut' (6) muncul berulang di timeline, menunjukkan lapisan kecemasan di balik euforia teknologi. Diskursus tak hanya soal kapabilitas, tapi dampak sosial otomasi.",
            "Beberapa tweet membingkai robot sebagai ancaman pengganti peran manusia, sementara lainnya melihatnya sebagai alat pemberdayaan. Tensi ini khas dalam transisi teknologi besar.",
            "Narasi kecemasan ini penting dibaca bersama euforia Microduck dan agen AI, sebab adopsi massa teknologi fisik akan bergantung pada seberapa masyarakat merasa diajak rather than diganti."
        ]
    }
]

pinggir_jurang_themes = [
    {
        "title": "Demonstrasi Depan DPR: Kekacauan atau Represi?",
        "summary": "Aksi massa di depan Gedung DPR berujung pembubaran paksa, gas air mata, dan kerahkan Brimob\u2014membangkitkan memori represi.",
        "body": [
            "Malam 27 Agustus 2026, massa aksi demonstrasi\u2014terutama mahasiswa dan berbagai elemen masyarakat\u2014berkumpul di depan Gedung DPR menuntut penolakan RUU Perampasan Aset. Narasi lapangan menyebut situasi 'se-chaos itu' bahkan setelah mahasiswa pulang.",
            "Respons aparat berupa pembubaran paksa, tembakan gas air mata, dan pengerahan pasukan Brimob memicu kecaman atas pendekatan keamanan yang berlebihan. Video Tempo menangkap massa berlari menghindari gas air mata dan bentrokan di depan gedung wakil rakyat.",
            "Tuduhan soal 'penunggang gelap' dan 'bohir chaos' yang dibalut narasi politik memperlihatkan upaya peredaman legitimasi aksi. Pertanyaan kritisnya: apakah kekacauan itu dari rakyat yang berunjuk rasa, atau dari cara negara merespons?"
        ]
    },
    {
        "title": "RUU Perampasan Aset dan Krisis Kepercayaan",
        "summary": "RUU yang dianggap mengancam hak milik rakyat memicu resistensi luas lintas lapisan.",
        "body": [
            "Akar demonstrasi adalah RUU Perampasan Aset yang dipandang mengancam hak properti warga. Penolakan datang tidak hanya dari mahasiswa, tapi berbagai lapisan masyarakat yang merasa terancam.",
            "Framing otoritas yang menyebut aksi sebagai 'demo penunggang gelap' gagal menutupi fakta bahwa tuntutan awal sebagian sudah dipenuhi di siang hari\u2014namun malam hari berubah jadi konfrontasi.",
            "Krisis ini mencerminkan lemahnya ruang dialog antara wakil rakyat dan konstituen. Ketika gedung DPR dikelilingi Brimob, yang hilang bukan cuma ketenangan malam, tapi kepercayaan pada prosedur demokratis."
        ]
    }
]

digest = {
    "generated_at": ISO,
    "techbro": {
        "tweets_total": tweets_total,
        "contributors": contributors,
        "themes": techbro_themes,
    },
    "tempo": {
        "count": total_tempo,
        "categories": {"groups": groups},
    },
    "pinggir_jurang": {
        "themes": pinggir_jurang_themes,
    },
    "youtube": youtube,
}

out = os.path.join(BASE, "data", f"digest_{STAMP}.json")
json.dump(digest, open(out, "w"), ensure_ascii=False, indent=2)
print("WROTE", out)
print("themes=", len(techbro_themes), "tempo=", total_tempo, "yt=", len(youtube))
