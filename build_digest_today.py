import json, datetime, collections

feed = json.load(open("data/feed_20260720.json"))
tempo = json.load(open("data/tempo_20260720.json"))
yt = json.load(open("data/tempo_yt_20260720.json"))
news = json.load(open("data/news_monitor_20260720.json"))

# ---------- techbro contributors ----------
tb = [t for t in feed["tweets"] if t.get("is_techbro_id")]
contrib = collections.Counter(t["user"] for t in tb)
contributors = [{"user": u, "count": n} for u, n in contrib.most_common()]

# ---------- tempo categories (mechanical) ----------
cat = collections.defaultdict(list)
for a in tempo["articles"]:
    cat[a["source"]].append(a)
groups = []
for c in ["tempo:nasional", "tempo:bisnis", "tempo:tekno"]:
    items = cat.get(c, [])
    groups.append({"category": c, "count": len(items),
                   "headlines": [a["title"] for a in items[:5]]})
linkmap = {a["title"]: (a["source"], a["link"]) for a in tempo["articles"]}

# ---------- prabowo scan (all tweets) ----------
pra_tweets = [t for t in feed["tweets"] if "prabowo" in t.get("text", "").lower()]
pra_critical = [t for t in pra_tweets if not t["text"].lower().startswith("semua ada masa")]
prabowo = {
    "tldr": ("Tidak ada kritik atau gaffe Prabowo yang menonjol hari ini — hanya satu cuitan netral "
             "@zainalamochtar yang menyebut namanya di luar konteks politik."),
    "points": [],
    "sample_tweets": [t["text"] for t in pra_tweets][:5]
}

# ---------- news watch ----------
nw_topics = []
for t in news["topics"]:
    sources = sorted(set(a["source"] for a in t["articles"]))
    arts = [{"title": a["title"], "link": a["link"], "source": a["source"]} for a in t["articles"][:5]]
    if t["topic"].lower().startswith("febri") or "febri" in t["topic"].lower():
        tldr = ("Kasus eks Jampidsus Febrie Adriansyah kembali memanas: Kejagung menegaskan status tersangka, "
                "pengacara Hotman Paris disebut terlibat, dan Gerindra meminta Hotman tak menyeret Prabowo.")
        points = [
            "Kejagung menegaskan status tersangka eks Jampidsus Febrie Adriansyah terkait kasus korupsi dan TPPU di tiga BUMN.",
            "Hotman Paris disebut sebagai pengacara Febrie; Gerindra melarangnya menyeret Presiden Prabowo ke dalam perkara.",
            "BBC dan CNN mengupas kronologi penggeledahan polisi di belasan lokasi serta peran PPATK yang siap bantu penyidikan.",
            "CNN melaporkan 'fakta-fakta baru' kasus Febrie yang memperluas tekanan publik pada lembaga penegak hukum."
        ]
    else:
        tldr = ("Topik KPK hari ini bersinggungan erat dengan kasus Febrie dan tata kelola antikorupsi, "
                "dengan sorotan pada komitmen zero-tolerance fraud di BNI.")
        points = [
            "Kasus Febrie Adriansyah (eks Jampidsus) jadi titik temu sorotan KPK terhadap korupsi di lembaga penegak hukum.",
            "BNI menegaskan zero tolerance terhadap fraud dan memperkuat tata kelola serta integritas perusahaan.",
            "BBC dan CNN merilis laporan kronologi penyidikan yang memperluas publikasi kasus ke ranah internasional.",
            "Tempo menyoroti kaitan antara perkara dan Istana, menambah debat soal batas kewenangan penegak hukum."
        ]
    nw_topics.append({"topic": t["topic"], "matches": t["matches"], "tldr": tldr,
                      "sources": sources, "points": points, "articles": arts})
news_watch = {"topics": nw_topics}

# ---------- youtube (prose from transcripts) ----------
youtube = {
    "tldr": ("Dari lima video Tempo, empat berhasil dirangkum dari transkrip/deskripsi: juara Piala Dunia Spanyol, "
             "aturan impor minyak Rusia via Lemigas, usulan pembatasan penerima MBG, kritik Kabinet Bayangan soal "
             "fiskal, dan cek fakta 'agen CIA palsu'. Satu video (MBG) transkripnya hanya musik sehingga dirangkum dari deskripsi."),
    "videos": [
        {"title": "Spanyol Juara Piala Dunia 2026", "url": "https://www.youtube.com/watch?v=bJa-QlBAue0",
         "channel": "tempodotco",
         "summary": ("Spanyol menjuarai Piala Dunia 2026 setelah mengalahkan Argentina 1-0 pada final di New York New "
                     "Jersey Stadium, Senin dinihari 20 Juli 2026. Gol tunggal Ferran Torres di babak tambahan "
                     "memastikan La Roja meraih gelar juara dunia."),
         "points": ["Spanyol juara dunia kedua dalam sejarah (setelah 2010).",
                    "Ferran Torres jadi penentu lewat gol di babak tambahan.",
                    "Final berlangsung di New York New Jersey Stadium, 20 Juli 2026."]},
        {"title": "Jelasin Dong! Aturan Spesial untuk Memuluskan Impor Minyak Rusia",
         "url": "https://www.youtube.com/watch?v=7u3PvlAQcz0", "channel": "tempodotco",
         "summary": ("Tempo mengupas Peraturan Menteri SDM No. 10/2026 yang mengubah tata kelola Lemigas sehingga "
                     "berubah dari konsultan menjadi trader sekaligus importir tunggal minyak Rusia, dengan Iksan "
                     "Kiat—yang punya jaringan di Rusia—ditunjuk mengeksekusi rencana itu."),
         "points": ["Lemigas bergeser dari konsultan menjadi trader dan importir tunggal minyak Rusia.",
                    "Permen SDM 10/2026 mengizinkan kepala Lemigas berasal dari non-PNS.",
                    "Iksan Kiat dipilih karena dianggap punya jaringan penguasa Rusia.",
                    "Aturan spesial ini muncul di tengah-tengah proses pengadaan minyak Rusia."]},
        {"title": "Prioritas MBG Diusulkan Hanya untuk Balita hingga Murid SMP",
         "url": "https://www.youtube.com/watch?v=1QviPj7kM6s", "channel": "tempodotco",
         "summary": ("Wakil Ketua Komisi IX DPR Yahya Zaini mengusulkan refocusing penerima manfaat Makan Bergizi "
                     "Gratis (MBG) diprioritaskan untuk balita dan siswa SMP, dengan alasan kelompok itu masih dalam "
                     "masa pertumbuhan yang membutuhkan asupan gizi tinggi."),
         "points": ["Usul dari Yahya Zaini (Wakil Ketua Komisi IX DPR) via pesan WhatsApp, 19 Juli 2026.",
                    "Alasan: balita & SMP masih dalam masa pertumbuhan butuh gizi tinggi.",
                    "Mengisyaratkan cakupan MBG terlalu lebar sehingga perlu dipersempit."]},
        {"title": "Menteri Kabinet Bayangan: Pajak Rakyat Dipakai Sembarangan",
         "url": "https://www.youtube.com/watch?v=binQ0nc0tyc", "channel": "tempodotco",
         "summary": ("Kabinet Bayangan menyoroti persoalan ekonomi dan tata kelola anggaran era Prabowo. Bhima "
                     "Yudhistira (Menteri Keuangan & Tata Kelola Anggaran Kabinet Bayangan) menuding anggaran negara "
                     "'dipakai sembarangan' tanpa akuntabilitas, menyebut program populis MBG dan Koperasi Desa "
                     "Merah Putih berjalan tanpa kajian dan pilot project."),
         "points": ["Bhima Yudhistira: anggaran dari pajak rakyat dipakai tanpa akuntabilitas.",
                    "Program populis MBG dan Koperasi Desa Merah Putih disebut tanpa kajian/pilot project.",
                    "Kritik langsung pada tata kelola fiskal pemerintahan Prabowo."]},
        {"title": "Laporan Tempo soal Agen CIA Palsu Dibantah, Benarkah Hoaks? | Cek Fakta",
         "url": "https://www.youtube.com/watch?v=gPKVECwu8TM", "channel": "tempodotco",
         "summary": ("Tim Cek Fakta Tempo menyimpulkan bahwa bantahan atas laporan investigasi 'Kisah Agen CIA Palsu "
                     "Menyusup ke Prabowo' adalah gerakan manipulasi informasi terorganisir. Laporan Tempo (28 Juni "
                     "2026) berbasis bukti konkret soal Gaurav Srivastava yang menjalin hubungan dengan Prabowo sejak 2020."),
         "points": ["Puluhan akun sebar narasi serupa hampir bersamaan — diduga terkoordinasi (#HoaxPenipuanPresiden).",
                    "Laporan Tempo didasarkan wawancara, dokumen, email, foto, dan berkas pengadilan.",
                    "Gaurav Srivastava menjalin hubungan dengan Prabowo sejak 2020; Kemhan terbitkan 3 surat ke perusahaan yang baru didirikan SETELAH surat itu.",
                    "Srivastava punya rekam jejak penipuan sejak 2014; Kemhan belum merespons penelusuran Tempo."]}
    ]
}

# ---------- techbro themes (prose by LLM) ----------
techbro = {
    "contributors": contributors,
    "tldr": ("Komunitas techbro hari ini pecah antara euforia Piala Dunia 2026—Spanyol dirayakan, Argentina "
             "dicerca sebagai 'cheater'—dan hiruk-pikuk build-in-public AI @vantis_ai, sementara @lynxluna, "
             "@__r17x, dan @ismailfahmi menyisipkan catatan soal LLM, infrastruktur, dan transformasi digital."),
    "themes": [
        {"title": "Euforia Piala Dunia 2026: Spanyol Rajang Argentina",
         "summary": "Piala Dunia 2026 jadi obrolan paling riuh di linimasa techbro, dengan @ainunnajib dkk merayakan kemenangan Spanyol sekaligus mengecam arbitrase yang dianggap memihak Argentina.",
         "body": [
             "@ainunnajib mendominasi linimasa dengan deretan retweet dan cuitan soal final: ia menyoroti bahwa Argentina 'had 0 shots in 90 minutes' dan mencibir wasit yang 'bailed out Argentina again', menutup dengan yel 'PALESTINE WON THE WORLD CUP! THANK YOU SPAIN'. Ia bahkan mempertanyakan taktik Argentina yang 'mati samasekali' dan menyebut Messi 'udah pensiun aja, dibantuin curang melulu', mencerminkan kekecewaan bercampur guyonan khas suporter.",
             "@ArdyaDipta melengkapi euforia dengan canda: 'YESSS TORRES 1-0 (seketika de javu 2008)', 'argentina selain Messi ga ad yg punya teknik makanya maennya kayak preman semua', dan 'it should've been Spain vs Egypt in the final'. @anvie ikut menambah nada kebangsaan lewat '🇪🇸 The best! 🔥' dan 'Spanyol FTW!', sementara @girikuncoro memberi selamat 'Congrats Spain on winning the world cup!'",
             "@ainurohman mencatat fakta statistik bahwa Argentina adalah 'tim pertama dalam sejarah yang mencatat NOL SHOTS dalam 90 menit di Final Piala Dunia', dan @MikaelDewabrata membandingkan final dengan sebutan 'fifa cheater'. Semangat bola ini jadi perekat sosial antar engineer yang biasanya asyik dengan kode, menunjukkan sisi humanis komunitas techbro."
         ]},
        {"title": "AI, Infrastruktur & Build-in-Public ala @vantis_ai",
         "summary": "Sisi builder techbro panas lewat @lucaxyzz yang pamer progres @vantis_ai dan @lynxluna yang berbagi eksperimen LLM, diiringi @__r17x soal infrastruktur Layer 0.",
         "body": [
             "@lucaxyzz jadi mesin penggerak hari ini: ia menegaskan 'AI Slop is prohibited', memamerkan bahwa 'Vantis just like a bootstrap version of $VVV, no VC, just from my savings', dan menandai 'Inflection pointnya di Feb 2026, Opus 4.6 bukan 4.5' sebagai momen yang mengubah cara kerja founder. Ia juga menulis 'Tokenized the data center' dan meretweet filosofi 'if you win the rat race, you're still a rat'.",
             "@lynxluna berbagi observasi bahwa seseorang 'capek ngeprompt ke LLM frontier, malah jadi nulis harness sendiri buat belajar Mandarin', mencerminkan ironi hobi engineer yang justru kembali ke kode saat model makin otonom. @__r17x menyumbang saran arsitektur: 'If you build something nowadays, ensure your infra aka Layer 0 was <GENERIC|Replaceable>', memilih Alchemy untuk UNI, serta menuturkan 'But I hope that the dream don't kill me before it's alive'.",
             "@arjunaskykok menyisipkan prediksi bisnis-olahraga bahwa 'FIFA will make World Cup a biennial event' dengan 64 negara—campuran antara obrolan bola dan korporasi yang khas techbro. Potret ini menunjukkan komunitas yang tetap produktif: antara membangun produk, menjaga infra, dan merefleksikan arah AI."
         ]},
        {"title": "Gaming, Film Kolosal & Hiburan",
         "summary": "Di luar kode, techbro berbagi hobi gaming dan kerinduan pada film kolosal Indonesia seperti Saur Sepuh.",
         "body": [
             "@lynxluna menghabiskan waktu dengan 'Sniper Elite Resistance: Devil Cauldron. Hard Mode, First Run' dan terlibat diskusi teknis soal sink audio 5.1, menunjukkan sisi gamer yang tak lepas dari detail teknis. @MikaelDewabrata mengajak 'guild dan butuh teman mabar buat event di hari Minggu', membawa nuansa komunitas gaming ke linimasa.",
             "Di sisi hiburan, @MikaelDewabrata menyerukan 'Saatnya hidupkan film-film kolosal khas Indonesia di masa lalu. Satu contoh itu Saur Sepuh', membagikan nostalgia akan sinetron legendaris dan meng-retweet channel yang mengunggah Saur Sepuh 1-5. @ArdyaDipta melengkapi dengan obrolan sehari-hari soal cemilan saat menonton final, menunjukkan techbro yang tetap manusiawi di luar codebase."
         ]},
        {"title": "Kewarganegaraan & Kritik Sosial",
         "summary": "Sejumlah techbro menyisipkan catatan soal transformasi digital institusi dan arah platform media sosial.",
         "body": [
             "@ismailfahmi membagikan refleksi soal 'mengapa dalam merencanakan dan memulai transformasi digital Muhammadiyah 4 tahun lalu, kami mengambil pelajaran dari...', menunjukkan sisi techbro yang terjun ke transformasi institusi keagamaan skala besar. Di tengah euforia Spanyol, @anvie tetap menancapkan nada kebangsaan yang sekaligus berbau pernyataan posisi.",
             "@jellypastaa menyebarkan 'An Open Letter to Elon Musk, Nikita Bier, and the X Team', sebuah surat terbuka yang di-retweet pula oleh @MikaelDewabrata, mencerminkan kepedulian techbro pada arah platform X. @lynxluna melengkapi dengan pesan berbahasa Sunda 'Postingkeun geura! Tong hilap polo beliau nya' yang menunjukkan sisi humanis di luar codebase."
         ]},
        {"title": "Engineering Wisdom & Realita Infrastruktur",
         "summary": "Techbro berbagi pelajaran praktis soal kerja, operasional, dan prinsip infrastruktur yang bisa diganti (replaceable).",
         "body": [
             "@__r17x menekankan prinsip desain infra: 'ensure your infra aka Layer 0 was <GENERIC|Replaceable>', memilih Alchemy untuk UNI sebagai lapisan yang bisa diganti—nasihat arsitektur yang sapient untuk builder pemula. Ia juga menyiratkan kelelahan membangun lewat 'But I hope that the dream don't kill me before it's alive'.",
             "@lucaxyzz merangkum filosofi startup lewat 'if you win the rat race, you're still a rat' dan penekanan bootstrap tanpa VC, sementara @arjunaskykok menyumbang catatan soal ekspansi FIFA. Potret ini menunjukkan techbro yang reflektif: antara membangun produk, menjaga infra, dan tetap kritis pada ekosistem yang mereka tinggali."
         ]}
    ]
}

# ---------- tempo pinggir_jurang (prose by LLM) ----------
def opp_article(title, why):
    src, link = linkmap.get(title, ("tempo:nasional", ""))
    return {"title": title, "link": link, "source": src, "why_opposition": why}

pj_themes = [
    {"title": "Kabinet Bayangan: Oposisi Sipil terhadap Prabowo",
     "summary": "Koalisi masyarakat sipil membentuk 'Kabinet Bayangan' sebagai pengawasan alternatif, dengan tuduhan anggaran dipakai sembarangan.",
     "body": [
         "Tempo menyoroti lahirnya 'Kabinet Bayangan' bentukan koalisi masyarakat sipil sebagai respons atas gaya pemerintahan Prabowo—sebuah framing oposisi yang eksplisit: artikel 'Alasan Koalisi Sipil Membentuk Kabinet Bayangan Prabowo' dan 'Fakta-fakta Kabinet Bayangan Bentukan Masyarakat Sipil' membingkai gerakan ini sebagai pengawasan independen di saat oposisi formal melemah.",
         "Dalam video 'Menteri Kabinet Bayangan: Pajak Rakyat Dipakai Sembarangan', Bhima Yudhistira (Menteri Keuangan & Tata Kelola Anggaran Kabinet Bayangan) menuding anggaran negara 'dipakai sembarangan' dan tak ada akuntabilitas, menyebut program populis seperti MBG dan Koperasi Desa Merah Putih berjalan 'tanpa kajian dan pilot project'. Ini adalah kritik langsung pada tata kelola fiskal era Prabowo."
     ]},
    {"title": "Kisruh Febrie & Upaya Menjauhkan Prabowo",
     "summary": "Tempo mengangkat ketegangan antara kuasa hukum eks Jampidsus Febrie dan kubu istana yang tak ingin presiden terseret perkara.",
     "body": [
         "Tempo melaporkan 'Gerindra Minta Hotman Tak Seret Prabowo dalam Kasus Febrie', mengangkat ketegangan antara pengacara eks Jampidsus Febrie Adriansyah—Hotman Paris—dan kubu istana. Hotman menyatakan polisi tak permisi ke Presiden saat menetapkan kliennya sebagai tersangka korupsi, memunculkan pertanyaan soal sejauh mana eksekutif terlibat dalam perkara penegakan hukum berdaya tinggi. Framing ini menempatkan Tempo di posisi menguak potensi intervensi presiden."
     ]},
    {"title": "Militerisasi & Ancaman Kebebasan Akademik",
     "summary": "Rentetan kebijakan mendekatkan militer ke ranah sipil dan menekan ruang akademik disorot Tempo dari sudut kritis.",
     "body": [
         "Tempo mengangkat kebijakan yang mendekatkan militer ke ranah sipil: 'Kemenkeu Libatkan Babinsa dalam Pengawasan Wajib Pajak' dan 'Prabowo Minta Tak Usah Pertanyakan TNI-Polri Turun ke Sawah' menunjukkan normalisasi peran tentara dalam urusan pajak dan pertanian—sebuah pengaburan batas sipil-militer yang disorot dari kacamata kritis.",
         "Di front akademik, 'SPK Soroti Ancaman Kebebasan Akademik dalam RUU Sisdiknas' dan 'FH UGM Kecam Intimidasi terhadap Dosen yang Kritik Mutasi PU' mencatat tekanan pada kebebasan berpendapat dan otonomi kampus. Tempo membingkai ini sebagai erosi ruang kritis di tengah legislasi pendidikan yang tertutup."
     ]},
    {"title": "Kebolongan Program Pro-Rakyat (MBG)",
     "summary": "Program andalan pemerintah Makan Bergizi Gratis dibongkar lubang tata kelolanya: serapan rendah dan tunggakan triliunan.",
     "body": [
         "Tempo membongkar inefisiensi program unggulan: 'BGN: Anggaran Program MBG 2025 Hanya Terserap 66 Persen' dan 'Tunggakan BGN Tahun Anggaran 2025 Capai Rp 1,6 Triliun' mempertontonkan lubang eksekusi pada program Makan Bergizi Gratis yang digadang-gadang sebagai flagship Prabowo.",
         "Tak hanya itu, 'Prioritas MBG Diusulkan Hanya untuk Balita hingga Murid SMP' (usul Yahya Zaini, Komisi IX DPR) mengisyaratkan cakupan program terlalu lebar sehingga perlu dipersempit—pengakuan terselubung bahwa desain awal MBG tak terukur. Tempo memakai rangkaian ini untuk menyoroti gap antara janji politik dan realitas di lapangan."
     ]}
]
pj_articles = [
    opp_article("Gerindra Minta Hotman Tak Seret Prabowo dalam Kasus Febrie",
                "Menguak potensi intervensi presiden dalam perkara hukum berdaya tinggi (eks Jampidsus Febrie)."),
    opp_article("Kemenkeu Libatkan Babinsa dalam Pengawasan Wajib Pajak",
                "Menyoroti militerisasi pengawasan pajak sipil yang mengaburkan batas tentara-warga."),
    opp_article("Alasan Koalisi Sipil Membentuk Kabinet Bayangan Prabowo",
                "Membingkai lahirnya oposisi sipil alternatif di tengah melemahnya oposisi formal."),
    opp_article("Menteri Kabinet Bayangan: Pajak Rakyat Dipakai Sembarangan",
                "Kritik tata kelola fiskal tanpa akuntabilitas pada program populis pemerintah."),
    opp_article("SPK Soroti Ancaman Kebebasan Akademik dalam RUU Sisdiknas",
                "Mencatat erosi kebebasan akademik lewat legislasi pendidikan yang tertutup."),
    opp_article("BGN: Anggaran Program MBG 2025 Hanya Terserap 66 Persen",
                "Membongkar inefisiensi program pro-rakyat andalan pemerintah."),
    opp_article("Tunggakan BGN Tahun Anggaran 2025 Capai Rp 1,6 Triliun",
                "Menunjukkan lubang tata kelola dan tunggakan pada program MBG.")
]
pinggir_jurang = {
    "tldr": ("Tempo hari ini menajamkan kritik lewat lahirnya Kabinet Bayangan sipil, kisruh hukum Febrie yang "
             "mencoba menjauhkan Prabowo, militerisasi ranah sipil, dan kebolongan program MBG—menempatkan media "
             "di pinggir jurang pengawasan kekuasaan."),
    "themes": pj_themes,
    "articles": pj_articles
}
tempo_section = {"pinggir_jurang": pinggir_jurang, "categories": {"groups": groups}}

# ---------- assemble ----------
now = datetime.datetime.now(datetime.timezone.utc)
digest = {
    "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "date": "20260720",
    "tldr": ("Techbro di linimasa larut dalam euforia Piala Dunia 2026 (Spanyol taklukkan Argentina) dan hiruk-pikuk "
             "build AI @vantis_ai, sementara Tempo menajamkan kritik lewat Kabinet Bayangan, kisruh Febrie, dan "
             "militerisasi sipil; topik berita panas bertumpu pada kasus Febrie Adriansyah dan KPK, dan Tempo merilis "
             "cek fakta soal 'agen CIA palsu'. Tak ada kritik Prabowo yang menonjol di timeline hari ini."),
    "techbro": techbro,
    "tempo": tempo_section,
    "youtube": youtube,
    "prabowo": prabowo,
    "news_watch": news_watch
}

with open("data/digest_20260720.json", "w") as o:
    json.dump(digest, o, ensure_ascii=False, indent=2)
print("WROTE data/digest_20260720.json")
print("techbro contributors:", len(contributors), "tweets:", len(tb))
print("opposition articles:", len(pj_articles))
print("youtube videos:", len(youtube["videos"]))
print("prabowo mentions:", len(pra_tweets), "(critical:", len(pra_critical), ")")
print("news topics:", [(t["topic"], t["matches"]) for t in nw_topics])
