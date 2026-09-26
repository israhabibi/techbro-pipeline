import json, collections

D = "20260727"
base = "/home/isra_habibi/techbro/data/"

feed = json.load(open(base + f"feed_{D}.json"))
tempo = json.load(open(base + f"tempo_{D}.json"))
yt = json.load(open(base + f"tempo_yt_{D}.json"))
nm = json.load(open(base + f"news_monitor_{D}.json"))

cnt = collections.Counter(t["user"] for t in feed["tweets"] if t.get("is_techbro_id"))
contributors = [{"user": "@" + u, "count": c} for u, c in cnt.most_common(6)]

techbro_themes = [
    {
        "title": "Peluncuran Vantis AI: Techbro Lokal Masuk Gelanggang Startup AI",
        "summary": "@lucaxyzz resmi meluncurkan @vantis_ai dan komunitas techbro Indonesia ramai memberi dukungan.",
        "body": [
            "Sorotan utama timeline hari ini adalah peluncuran Vantis AI oleh @lucaxyzz. Dalam cuitannya ia berterima kasih pada semua yang hadir di acara peluncuran dan menegaskan visinya: 'Kita launching @vantis_ai for good. AI will create more jobs.' Ia juga mengumumkan bahwa token proyeknya sudah terdaftar (listed) di CoinGecko, menandai langkah serius masuk ke ranah AI sekaligus kripto.",
            "Dukungan mengalir dari sesama warga X. @ghozyulhaq hadir langsung di acara dan menyebut @lucaxyzz sebagai 'techbro favorit warga X', cuitannya di-retweet oleh @ainunnajib. Di sela-sela itu @lucaxyzz tetap menampilkan gaya khasnya yang santai — bercanda soal kebiasaan mepet deadline dan alasan menolak meeting: 'kan aku ownernya'.",
            "Peluncuran ini jadi momen jarang di mana komunitas techbro Indonesia berkumpul offline, memperlihatkan ekosistem builder lokal yang mulai berani meluncurkan produk AI sendiri alih-alih sekadar mengomentari tren dari luar."
        ]
    },
    {
        "title": "AI Coding Agents Mengubah Cara Kerja: Hermes, GPT5.6-SOL, dan Vibe Coding",
        "summary": "Para engineer senior berbagi pengalaman nyata memakai agentic AI dalam workflow harian mereka.",
        "body": [
            "@anvie mengamati bahwa sejak memakai agentic AI untuk coding, gaya coding para engineer ikut berubah — meski ia menegaskan 'rg, vi, and sed is enough for me when AI ngadat'. Ia juga membedah perilaku model terbaru: 'Salah satu yg saya notice dari GPT5.6-SOL ini adalah dia lebih suka menggunakan patch daripada str_replace' dalam mengedit kode.",
            "@ainunnajib ikut memuji tooling terbaru, menyebut kombinasi 'Hermes + 5.6 Sol powerful banget'. Ia bahkan memakai AI untuk hal tak terduga: menyuruh agent men-scrape TLX untuk membandingkan peserta latihan soal OSP dengan daftar yang lolos OSK, lengkap dengan gsheet hasilnya yang ia bagikan ke publik.",
            "@ismailfahmi menggambarkan sisi lain dari tren ini: 'Semalem ngelembur vibe coding. Pagi2 tadi istirahat dulu, karena token habis, nunggu reset.' Sementara di sisi frontend, @__r17x sibuk membahas rilis ekosistem Effect ('Say good bye to effect-query!') dan eksperimen Suspense di React — dikomentari @hasgardians yang menyebut changelog Effect v4 'berasa baca patch dota'."
        ]
    },
    {
        "title": "Regenerasi Talenta: OSN Informatika dan Cerita Dzuizz & Habibie",
        "summary": "@ainunnajib mendokumentasikan perjalanan anak-anak muda Indonesia menuju olimpiade komputer.",
        "body": [
            "@ainunnajib membagikan momen 'Dzuizz & Habibie belajar olimpiade komputer bersama', lengkap dengan throwback foto mereka mulai belajar bersama pada 2021 — lima tahun lalu. Hari ini keduanya bersiap menghadapi OSN Provinsi Informatika, dan ia meminta doa dari timeline.",
            "Cuitan ini memantik nostalgia soal akses pendidikan. @ArdyaDipta menimpali soal majalah Bobo di perpustakaan sekolah, sementara @ainunnajib bercerita 'abah saya yang PNS dulu mengupayakan 1 & 2, kalau perlu ngutang' — refleksi bahwa akses ke bahan belajar dulu adalah kemewahan. @giIangmahesa ikut menyoroti peluang bagi kampus: 'Mana nih kampus2 Indonesia, ada tawaran menarik ini', yang di-retweet @MikaelDewabrata.",
            "Tema regenerasi talenta digital ini melengkapi kabar @ainunnajib lain: 'asik ada yang ke NTU' — anak-anak binaan komunitas competitive programming Indonesia mulai menembus kampus top Asia."
        ]
    },
    {
        "title": "Etika Warga X: Kasus KS, Doxxing, dan Kampanye Anti-Scam",
        "summary": "Timeline techbro juga bergulat dengan sisi gelap media sosial dan inisiatif melawan penipuan online.",
        "body": [
            "@lynxluna banyak me-retweet seruan agar kasus kekerasan seksual tidak diperlakukan seperti infotainment — mengangkat suara @tikaalmira, @rahmaut, dan @petitstardust yang mengkritik penyebaran foto keluarga korban serta budaya 'guilty by association' yang menyasar orang-orang yang justru membantu korban seperti @F2aldi. Cuitan @nezhifi yang ia RT bahkan menyindir ekspektasi absurd publik: 'pada berharap techbro ngapain si Prima sih? terbang ke negara lain?'",
            "Di jalur yang lebih konstruktif, @MikaelDewabrata mengumumkan rencana event offline gratis untuk awareness kampanye SCAM dari ASEAN, mengajak peserta ikut tanpa biaya. Ia juga aktif mengomentari dinamika platform, me-retweet kritik terhadap Musk: 'He literally bought the entire platform so we would listen.'",
            "@lucaxyzz menutup dengan observasi ringan tapi mengena soal temperamen platform: 'Hmmm iya juga ya, mudah tersulut apalagi warga X' — pengingat bahwa komunitas ini sadar betul karakter medan tempat mereka berkumpul."
        ]
    }
]

articles = [
    {"title": a["title"], "url": a["link"], "category": a["source"].split(":")[-1]}
    for a in tempo["articles"][:40]
]

pinggir_themes = [
    {
        "title": "Kasus Febrie Adriansyah: Tersangka VVIP dan Desakan Pansus Angket",
        "summary": "Penahanan eks Jampidsus Febrie Adriansyah memicu kritik soal perlakuan istimewa dan lemahnya pengawasan DPR.",
        "body": [
            "Tempo menurunkan 'Formappi Desak DPR Bentuk Pansus Angket Kasus Febrie' — Formappi menilai wewenang panja tim pengawas bentukan Komisi III DPR terlalu kecil untuk menyelidiki kasus korupsi Febrie Adriansyah. Kritik senada muncul dalam 'PDIP Kritik Febrie Adriansyah yang Terima Keistimewaan', menyoal perlakuan berbeda terhadap tersangka berstatus tinggi.",
            "Sentimen ini menggema di media sosial: cuitan yang di-retweet @ainunnajib menyindir 'Asik ya jadi tersangka VVIP. Ga pakai rompi dan borgol' — kontras dengan tersangka biasa. Kanal YouTube Tempo juga menayangkan 'Sutrimo yang Tewas Diduga Kepala Rumah Tangga Eks Jampidsus', menambah lapisan misteri pada kasus ini, serta 'Polri Didesak Tiru Kejaksaan dalam Kasus Firli Bahuri' yang menagih kesetaraan penegakan hukum."
        ]
    },
    {
        "title": "Kepuasan Publik Anjlok dan Retorika 'Londo Ireng'",
        "summary": "Survei menunjukkan penurunan tajam kepuasan terhadap pemerintah, sementara pernyataan Prabowo soal wartawan-LSM menuai kecaman.",
        "body": [
            "Dua artikel Tempo menohok: 'SMRC: Kepuasan Publik terhadap Kinerja Prabowo Turun 30 Persen' dan 'Cuma 13 Persen yang Nilai Kondisi Politik Nasional Baik'. Hasto pun angkat bicara dalam 'Respons Hasto soal Penurunan Kepuasan Publik ke Pemerintah', menandai tekanan politik yang meningkat terhadap pemerintahan.",
            "Di saat bersamaan, artikel 'Kala Prabowo Sebut Londo Ireng Kini Berbaju Wartawan-LSM' dan 'MTI: Ucapan Londo Ireng Prabowo Upaya Mendelegitimasi Pengawasan Publik' menyoroti retorika presiden yang dinilai menyerang pers dan masyarakat sipil — tepat ketika kepercayaan publik sedang merosot. Kritik ekonomi juga muncul lewat 'Kata Ekonom soal Pernyataan Prabowo Ekonomi Ilmu Sederhana'."
        ]
    },
    {
        "title": "Dinasti Politik Jalan Terus: Kaesang Bidik DPR, Jokowi Safari Politik",
        "summary": "Manuver keluarga Jokowi kembali jadi sorotan menjelang Pemilu 2029.",
        "body": [
            "Tempo memberitakan 'Kaesang Pangarep Bidik Kursi DPR di Pemilu 2029' dan strategi kandangnya dalam 'Kaesang Akan Maju Pileg dari Dapil 5 Solo, Strategi Bangun Kandang Gajah' — upaya membangun basis politik di kampung halaman keluarga. Ganjar merespons diplomatis lewat 'Ganjar PDIP Hormati Niat Kaesang Maju Pileg 2029 di Solo'.",
            "Sang ayah pun tak diam: 'Jokowi Bakal Lanjutkan Safari Politik ke NTT pada 31 Juli' menunjukkan mantan presiden masih aktif merawat jejaring politik. Semua ini terjadi ketika PDIP memperingati '30 Tahun Kudatuli, Megawati Beri 5 Instruksi bagi Kader PDIP' — panggung politik keluarga versus partai banteng kembali memanas."
        ]
    },
    {
        "title": "Infrastruktur Publik Bermasalah: Sekolah Rusak dan Kekerasan di Papua",
        "summary": "Kondisi sekolah negeri yang memprihatinkan dan kekerasan bersenjata di Yahukimo menguji klaim pembangunan.",
        "body": [
            "Artikel 'Alasan DKI Hanya Perbaiki 11 dari 22 Sekolah Rusak pada 2026' dan 'Kemendikdasmen Bakal Revitalisasi SDN Tanggirejo yang Viral' menggambarkan lambannya penanganan sekolah rusak; Gubernur Jakarta sampai harus 'Bentuk Tim Investigasi Bangunan Sekolah'. Temuan kesehatan pun mengejutkan: 'Temuan Cek Kesehatan Gratis: 1,9 Juta Siswa Hipertensi'.",
            "Dari timur, 'TPNPB-OPM Ungkap Alasan Penembakan 3 Warga Sipil di Yahukimo' dan permintaan dialog dalam 'KSP Kaji Surat Permintaan Dialog Forum Gereja soal Papua' menunjukkan konflik Papua masih jauh dari selesai. Sementara itu Celios menyuarakan kekhawatiran akademik lewat 'Celios Surati Russell Group Soal Risiko Proyek 10 Kampus URI'."
        ]
    }
]

videos = [{"title": v["title"], "url": v["url"], "channel": "Tempodotco"} for v in yt["videos"]]

digest = {
    "date": D,
    "techbro": {"themes": techbro_themes, "contributors": contributors},
    "tempo": {"articles": articles, "pinggir_jurang": {"themes": pinggir_themes}},
    "youtube": {"videos": videos},
    "prabowo": {
        "points": [
            "Survei SMRC mencatat kepuasan publik terhadap kinerja Prabowo turun 30 persen, dan hanya 13 persen responden menilai kondisi politik nasional baik.",
            "Ucapan Prabowo yang menyebut 'Londo Ireng' kini berbaju wartawan-LSM dikecam MTI sebagai upaya mendelegitimasi pengawasan publik terhadap pemerintah.",
            "Pernyataan Prabowo bahwa ekonomi adalah 'ilmu sederhana' dikritik ekonom karena dinilai menyederhanakan persoalan ekonomi yang kompleks."
        ]
    },
    "news_watch": {"topics": nm["topics"]},
}

out = base + f"digest_{D}.json"
with open(out, "w") as fp:
    json.dump(digest, fp, ensure_ascii=False, indent=2)
print("WROTE", out)
