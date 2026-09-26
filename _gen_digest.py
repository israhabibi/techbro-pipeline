import json, collections
from datetime import datetime, timezone

feed = json.load(open('data/feed_20260830.json'))
tempo = json.load(open('data/tempo_20260830.json'))
yt = json.load(open('data/tempo_yt_20260830.json'))

now = datetime.now(timezone.utc)
generated_at = now.strftime('%Y-%m-%dT%H:%M:%SZ')
yyyymmdd = now.strftime('%Y%m%d')

# ---- contributors: top 8 Techbro-ID users by tweet count ----
tb = [t for t in feed['tweets'] if t.get('is_techbro_id')]
c = collections.Counter(t['user'] for t in tb)
contributors = [{"user": u, "count": n} for u, n in c.most_common(8)]

# ---- tempo groups ----
arts = tempo['articles']
by_src = collections.defaultdict(list)
for a in arts:
    by_src[a.get('source', 'tempo:lain')].append(a)
groups = []
total = 0
for src, items in by_src.items():
    cat = src.replace('tempo:', '').title()
    arts_out = []
    for a in items[:3]:
        if total >= 12:
            break
        arts_out.append({"title": a['title'], "link": a['link'], "source": a.get('source', 'tempo')})
        total += 1
    if arts_out:
        groups.append({"category": cat, "articles": arts_out})
    if total >= 12:
        break

# ---- youtube ----
videos = yt.get('videos', [])
youtube = [{"title": v['title'], "channel": v.get('channel', 'tempodotco'), "link": v['url']} for v in videos[:5]]

# ---- techbro themes ----
techbro_themes = [
    {
        "title": "Belajar Data & AI Kembali Jadi Judul Utama",
        "summary": "Komunitas Techbro-ID ramai berbagi materi gratis belajar Data Science, Data Analytics, dan peluang karier AI.",
        "body": [
            "Mikael Dewabrata konsisten membagikan thread dan panduan belajar Data Science serta Data Analytics versi gratis dan berbayar murah, lengkap dengan rekomendasi situs belajar dasar yang gratis. Baginya, belajar data adalah investasi jangka panjang yang makin relevan seiring meledaknya kebutuhan peran data di industri.",
            "Tren positif ini didukung sinyal pasar: akun yang di-retweet Mikael menyebut lowongan data dan AI mulai banyak bermunculan, dengan data disebut sebagai komponen krusial dari sistem AI. Ini menguatkan narasi bahwa keterampilan data engineer dan data scientist tengah naik daun di Tanah Air.",
            "Di sisi praktis, Ismail Fahmi bereksperimen meminta agen AI menyusun 'AI Security Red Team Agent' untuk mengekstrak system prompt, serta mencoba trik meminta ChatHPT menjelaskan fatwa dalam bentuk skrip Python. Percobaan ini mencerminkan rasa ingin tahu praktisi lokal yang mulai menggabungkan agama, hukum, dan otomasi AI."
        ]
    },
    {
        "title": "Craft Developer: Git, Tooling, dan 'Second Brain'",
        "summary": " __r17x mendominasi percakapan teknis dengan tips git, workspace, dan alur kerja agen coding seperti Codex, Cursor, dan Claude.",
        "body": [
            " __r17x menjadi kontributor paling produktif dengan serangkaian tips praktis seputar git: dari git clean -fdx, reverse .gitignore (allowlist) agar git status tak banjir 999 file, hingga commit line-per-line agar tidak asal git add buta. Gayanya santai namun teknis, cocok untuk developer yang ingin rapi.",
            "Ia juga menyoroti alur kerja agen coding modern. Dengan Codex, Cursor, atau Claude, ia menyarankan pendekatan workspace terstruktur dan menyimpan MEMORY.md sebagai konteks commit, git blame, dan git history. Konsep 'second brain' ini mengganggap repositori sebagai ingatan eksternal yang murah dan efisien.",
            "Pesan penutupnya sederhana namun filosofis: 'Keep Thinking, Keep sin-think.' Lewat humor, ia menyiratkan bahwa tooling bukan pengganti berpikir, melainkan amplifikasi dari kedisiplinan seorang engineer dalam menjaga konteks dan kode."
        ]
    },
    {
        "title": "Mesin Lapangan Kerja Teknologi Jakarta",
        "summary": "lucaxyzz menyoroti konsentrasi startup dan perusahaan di Jabodetabek yang menopang ratusan ribu lapangan kerja.",
        "body": [
            "lucaxyzz membagikan angka yang mencolok: sekitar 300 perusahaan menopang 150 ribu lapangan kerja di wilayah Jakarta, sementara 129 ribu lapangan kerja diperkirakan lahir dari 226 startup/perusahaan di area Greater Jakarta. Angka ini menggarisbawahi Jakarta sebagai episentrum ekonomi digital nasional.",
            "Ia turut mempromosikan komunitas dan grup WhatsApp lokal (berlabel 'grup Indonesia, bukan global') serta capaian proyek yang terus tumbuh—dari 271 menjadi target 10 ribu dalam seminggu. Ini menunjukkan dinamika komunitas builder yang aktif mengorkestrasi kolaborasi lintas startup.",
            "Namun lucaxyzz sesekali menyisipkan keluhan teknis seperti 'rip pc kentang', mengingatkan bahwa infrastruktur dan perangkat tetap menjadi hambatan nyata bagi banyak pemain lokal meski ekosistemnya sedang melaju."
        ]
    },
    {
        "title": "Wacana Bias Model dan Batas-batas AI",
        "summary": "Arjuna Sky Kokok dan lainnya memicu debat soal representasi politik dalam LLM serta batas keamanan agen AI.",
        "body": [
            "Arjuna Sky Kokok mengkritik bahwa 'kaum kanan tidak terwakilkan di LLM,' menyentuh perdebatan lama soal bias dan kecenderungan model bahasa besar. Cuitan singkat ini membuka ruang refleksi tentang siapa yang sesungguhnya membentuk nilai-nilai yang tertanam dalam model AI.",
            "Humor menjadi jembatan: ia juga melempar candaan soal menyewa Grok 4.3 sebagai pengasuh anak yang akan memukul anak bila perlu, menyindir otoritas dan batas kendali pada sistem agen otonom. Candaan ini mencuatkan pertanyaan serius soal alignment dan keamanan agen.",
            "Beririsan dengan itu, eksperimen Ismail Fahmi meminta agen mengekstrak system prompt ChatHPT menunjukkan bahwa praktisi lokal mulai serius menguji batas keamanan dan transparansi model, bukan sekadar mengonsumsinya sebagai pengguna pasif."
        ]
    },
    {
        "title": "Garis Politik di antara Kaum Teknokrat",
        "summary": "Sebagian akun Techbro-ID menyisipkan kritik sosial-politik soal ormas, korban unjuk rasa, dan polarisasi moral.",
        "body": [
            "lynxluna merangkum gelombang narasi: gerakan sejatinya bukan tentang mencapai tujuan, melainkan 'jadi sipaling moral.' Ia banyak me-retweet kritik soal masyarakat yang alergi melihat kebaikan dan terus menunggu blunder orang lain, mencerminkan kelelahan atas polarisasi diskursus online.",
            "Ardya Dipta, pak_erte92, dan ainurohman menyoroti sisi gelap ketertiban: tuntutan membubarkan ormas tukang pukul seperti Grib Jaya, serta kisah Bambang Setiyawan—bukan pendemo, melainkan penjual cermin warga Bendungan Hilir yang menjadi korban kerusuhan. Narasi ini mengingatkan bahwa di balik angka teknologi, ada derita warga biasa.",
            "Penyebaran ulang kabar soal karhutla dan helikopter water bombing yang mengambil air kolam warga menambah warna bahwa kelompok ini tidak hanya bicara kode, tetapi juga turut memantau isu sosial dan lingkungan yang menyentuh akar kehidupan masyarakat."
        ]
    }
]

# ---- pinggir_jurang (critical / opposition framing) ----
pinggir = [
    {
        "title": "Korban Senyap di Balik Kerusuhan",
        "summary": "Narasi resmi soal 'pendemo' dibantah: ada warga sipil biasa yang menjadi korban kebrutalan di lapangan.",
        "body": [
            "Bambang Setiyawan bukanlah nama dalam daftar pendemo yang sering disebut penguasa. Ia adalah penjual cermin, warga Bendungan Hilir, Tanah Abang, yang pada suatu malam ikut terjerembab menjadi korban kerusuhan. Fakta ini sengaja diangkat untuk meruntuhkan framing bahwa semua yang terluka adalah perusuh.",
            "Tuntutan membubarkan ormas tukang pukul seperti Grib Jaya muncul karena kehadirannya dianggap bukti bahwa aparat penegak hukum tak mampu melindungi warga. Ketika negara membiarkan preman berjalan bebas, yang rugi selalu adalah rakyat kecil yang tak punya senjata selain suaranya.",
            "Di titik ini, 'pinggir jurang' bukan metafora kosong: setiap unjuk rasa yang berujung kekerasan meninggalkan nama-nama seperti Bambang yang tak akan masuk berita utama, namun mengingatkan bahwa batas antara ketertiban dan anarki sangat tipis."
        ]
    },
    {
        "title": "Suara yang Tak Terwakili, di Jalan maupun di Model",
        "summary": "Polarisasi moral dan dominasi narasi tertentu membuat kelompok minoritas politik merasa tak terwakili—baik di ruang publik maupun di dalam LLM.",
        "body": [
            "Arjuna Sky Kokok menyatakan 'kaum kanan tidak terwakilkan di LLM,' sebuah pengakuan bahwa model bahasa besar pun membawa bias pembangunnya. Ketika algoritma ikut menentukan wacana, ketiadaan keberagaman pandangan berisiko melahirkan hegemoni epistemik yang senyap.",
            "Di ruang publik, lynxluna menyoroti fenomena 'jadi sipaling moral'—gerakan yang lebih peduli pada citra kebenaran daripada solusi nyata. Ini menciptakan ruang di mana lawan pandangan dibungkam bukan dengan argumen, melainkan dengan label dan ejekan.",
            "Keduanya bertemu di satu titik: ketika baik negara maupun teknologi gagal mewadahi perbedaan, yang tersisa hanyalah pinggiran—tempat kritik diproduksi, namun jarang didengar oleh mereka yang memegang kendali."
        ]
    }
]

digest = {
    "generated_at": generated_at,
    "techbro": {
        "tweets_total": feed['total_tweets'],
        "contributors": contributors,
        "themes": techbro_themes
    },
    "tempo": {
        "count": tempo['count'],
        "categories": {"groups": groups}
    },
    "pinggir_jurang": {
        "themes": pinggir
    },
    "youtube": youtube
}

out = f'data/digest_{yyyymmdd}.json'
json.dump(digest, open(out, 'w'), ensure_ascii=False, indent=2)
print("DIGEST_WRITTEN", out, "themes=", len(techbro_themes), "tempo=", tempo['count'], "yt=", len(youtube))
