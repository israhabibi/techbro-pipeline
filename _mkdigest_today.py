import json, collections, datetime, os, re

D = "/home/isra_habibi/techbro"
day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
feed = json.load(open(f"{D}/data/feed_{day}.json"))
tempo = json.load(open(f"{D}/data/tempo_{day}.json"))
yt = json.load(open(f"{D}/data/tempo_yt_{day}.json"))

tw = feed["tweets"]
tb = [t for t in tw if t.get("is_techbro_id")]
cnt = collections.Counter(t["user"] for t in tb)
contributors = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
  {"title": "AI Coding dan Kecemasan Nilai Seorang Programmer",
   "summary": "Perdebatan soal vibecoding dan model murah bikin lini masa techbro Indonesia gelisah soal masa depan skill engineering.",
   "body": [
     "Percakapan paling panas hari ini datang dari @lynxluna yang menyindir 'tekbro pengendorse vibecoding' karena dianggap membuat programmer makin tidak laku. Sindiran itu bukan sekadar lelucon; ia menyambung utas panjangnya sendiri soal bagaimana ia dulu 'teriak-teriak bunyiin alarm' ketika skill issue bertemu dengan pilihan karier yang makin menyempit karena keadaan di luar kendali individu.",
     "Ia lalu membingkainya dalam garis waktu yang getir: pada 2024 orang masih menghibur diri bahwa Claude terlalu mahal sehingga tidak semua orang mampu, sementara dua tahun kemudian argumen harga itu runtuh. @lucaxyzz memperkuat nada yang sama dari sisi berlawanan, bercanda bahwa kegagalannya di bangku kuliah kini tertolong AI, dan bahkan menawarkan membayari orang yang mau memakai model flash generasi baru.",
     "Yang muncul dari dua kutub ini adalah satu ketegangan yang belum selesai: AI menurunkan biaya masuk ke dunia rekayasa perangkat lunak sekaligus mengikis premi keahlian yang dulu jadi tiket kelas menengah teknologi. Tidak ada yang menawarkan jawaban; yang ada hanya humor defensif dan kecemasan yang dibungkus meme."]},
  {"title": "Budaya Kerja Lintas Zona Waktu dan Romantisasi Kelelahan",
   "summary": "Obrolan @petrabarus dan @ArdyaDipta membuka jendela ke normalisasi jam kerja remote yang menggerus batas siang dan malam.",
   "body": [
     "@ArdyaDipta bertanya polos kapan @petrabarus sempat tidur setelah menyelesaikan workshop, dan dijawab dengan slogan lawas industri: 'Sleep is for the weak.' Candaan itu berlanjut ke pengakuan yang lebih substantif bahwa bekerja dengan zona waktu Amerika Serikat justru terasa nyaman karena tidak bentrok dengan jam kerja lokal.",
     "Pola yang ia gambarkan cukup jelas: siang dipakai bekerja, malam dipakai belajar. Bagi sebagian orang ini terdengar seperti disiplin, tetapi bagi yang lain ini adalah dua pekerjaan penuh yang dijalankan dalam satu tubuh. @ArdyaDipta di sisi lain memuji kantornya yang hampir tiap hari menyediakan workshop dan enablement daring, seolah pembelajaran korporat menambal jurang yang sama.",
     "Yang tidak dibicarakan adalah harganya. Kombinasi kerja lintas zona waktu, tekanan belajar mandiri, dan budaya yang memuji ketahanan begadang membentuk standar diam-diam bagi engineer muda Indonesia: kalau tidak lelah, mungkin kamu tidak cukup serius."]},
  {"title": "Crab Mentality dan Kritik Diri Kolektif",
   "summary": "@ainunnajib memantik diskusi soal mentalitas kepiting yang ia sebut khas Indonesia, dan tanggapan yang datang tidak sepenuhnya setuju.",
   "body": [
     "@ainunnajib melempar klaim tajam bahwa crab mentality sayangnya bersifat unik Indonesia, lalu memperkuatnya dengan menyatakan bahwa bahkan masyarakat Malaysia dan Filipina yang secara kultural berdekatan tidak menunjukkan pola yang sama. Klaim semacam ini selalu berisiko, karena mengubah pengalaman personal menjadi diagnosis nasional.",
     "@lynxluna dan @itsTimWijaya ikut dalam utas itu. @lynxluna menjawab dengan nada yang setengah percaya setengah menggoda, menyebut ia pernah mendengar cerita-cerita serupa, sebelum menutup diskusi dengan lelucon bahwa semuanya salah kepiting. Humor itu berfungsi sebagai katup, meredakan sesuatu yang sebenarnya menyakitkan untuk dibahas serius.",
     "Percakapan ini menarik bukan karena kesimpulannya, melainkan karena polanya. Komunitas teknologi Indonesia berulang kali kembali ke pertanyaan mengapa keberhasilan sesama sulit dirayakan, dan setiap kali jawabannya berhenti di tingkat karakter bangsa alih-alih struktur insentif yang membuat orang saling menjatuhkan."]},
  {"title": "Ekosistem Lokal: AWS Summit, Pertahanan, dan Cerita Perangkat Keras",
   "summary": "Dari keramaian AWS Summit Jakarta hingga uji coba USV Kamikaze PT PAL, lini masa menunjukkan lapisan industri yang lebih keras.",
   "body": [
     "@petrabarus melaporkan AWS Summit Jakarta 'tumpek plek' dan meminta cerita pengalaman peserta, sebuah pengingat bahwa konferensi vendor masih menjadi titik kumpul terbesar komunitas teknologi Indonesia. Antusiasme itu berdiri di atas basis pengguna cloud yang terus tumbuh sekaligus pemasaran korporat yang agresif.",
     "Di jalur berbeda, @Jatosint membagikan foto-foto baru dari PT PAL Indonesia yang memperlihatkan pengujian USV Kamikaze di dekat Jembatan Suramadu. Konten OSINT semacam ini menempatkan diskusi teknologi Indonesia di ranah yang jarang disentuh startup: pertahanan, manufaktur berat, dan kapabilitas negara.",
     "@lynxluna melengkapi spektrum dengan menyederhanakan sirkuit DRAM menjadi 'cuma mosfet dan kapasitor', sebuah provokasi yang menyindir betapa mudahnya orang meremehkan kompleksitas manufaktur semikonduktor. Tiga percakapan ini bersama-sama menggambarkan ekosistem yang jauh lebih luas daripada sekadar aplikasi dan pendanaan."]},
  {"title": "Migrasi, Bahasa, dan Bayangan Ekonomi Regional",
   "summary": "Wacana pindah negara dan belajar Mandarin muncul sebagai strategi bertahan personal di tengah ketidakpastian dalam negeri.",
   "body": [
     "@lynxluna secara terbuka menyinggung keinginan kabur atau menjadi warga Malaysia, dan menambahkan bahwa langkah paling optimal adalah belajar Mandarin lebih dulu. Ia juga sempat berkomentar bahwa bahasa Cina memang sulit tetapi tetap membuka jalan menuju keuntungan finansial, sebuah pragmatisme yang tidak disembunyikan.",
     "Nada ini tidak berdiri sendiri. Ia berdampingan dengan retweet-nya soal dugaan penyalahgunaan pinjaman ratusan triliun dari bank BUMN, yang menunjukkan bahwa keinginan pergi bukan semata soal gaji melainkan soal kepercayaan terhadap pengelolaan ekonomi domestik.",
     "Bagi kelas profesional teknologi Indonesia, mobilitas internasional adalah privilese sekaligus katup pelepas tekanan. Ketika mereka yang paling mampu pergi mulai membicarakan kepergian secara terbuka di lini masa publik, itu adalah sinyal yang layak dicatat oleh siapa pun yang peduli pada retensi talenta."]},
]

# tempo categorization
arts = tempo["articles"]
RULES = [
 ("Ekonomi & Bisnis", r"bank|kredit|ihsg|saham|bbm|pertamina|obligasi|bond|ojk|investasi|reksa|ekonomi|bisnis|merger|garuda|goto|hyundai|pegadaian|asuransi|umkm|pasar"),
 ("Energi & Infrastruktur", r"pln|listrik|pipa|gas|infrastruktur|proyek|psel|jalan|off ramp|air bersih|pdam|satelit|tol|pembangunan"),
 ("Hukum & Politik", r"kpk|korupsi|dpr|dprd|ruu|kapolri|polri|pidana|kejaksaan|narkotika|sita|selundup|ilegal|bareskrim|pn jakpus|partai|ppp|aset"),
 ("Sosial & Layanan Publik", r"bpjs|dukcapil|sekolah|pendidikan|kesehatan|stunting|baznas|bantuan|sosial|anak|disabilitas|pangan|transmigrasi|taspen|jkn"),
 ("Teknologi & Digital", r"digital|teknologi|ai |startup|aplikasi|data|internet|inovasi|ikd"),
]
groups = collections.OrderedDict()
used = []
for a in arts:
    t = a["title"].lower()
    cat = None
    for name, pat in RULES:
        if re.search(pat, t):
            cat = name; break
    if not cat:
        cat = "Nasional Lainnya"
    groups.setdefault(cat, [])
    if len(groups[cat]) < 3:
        groups[cat].append({"title": a["title"], "link": a["link"], "source": a["source"]})
        used.append(a)

glist = [{"category": k, "articles": v} for k, v in groups.items() if v]
total = sum(len(g["articles"]) for g in glist)
while total > 12:
    g = max(glist, key=lambda x: len(x["articles"]))
    g["articles"].pop()
    glist = [g for g in glist if g["articles"]]
    total = sum(len(g["articles"]) for g in glist)

pinggir = [
  {"title": "Ketika Berita Nasional Menjadi Etalase Pemerintah Daerah",
   "summary": "Sebagian besar kanal nasional hari ini diisi rilis apresiasi DPRD dan seremoni pejabat, bukan pengawasan kekuasaan.",
   "body": [
     "Dari puluhan artikel kanal nasional yang terkumpul hari ini, deretan teratas didominasi kabar DPRD Kota Bogor mengapresiasi pelatihan tepung mocaf, memperkuat ketahanan pangan, berharap off ramp mengurai kemacetan, dan mengapresiasi kinerja Polri. Empat berita, satu institusi, semuanya positif.",
     "Pola ini adalah gejala yang layak dikhawatirkan. Ketika ruang berita nasional dipenuhi materi yang secara struktur menyerupai siaran pers, publik kehilangan kemampuan membedakan mana laporan jurnalistik dan mana pemasaran politik yang dibiayai anggaran daerah. Yang hilang bukan hanya kualitas informasi, melainkan fungsi pers sebagai pengimbang kekuasaan.",
     "Di sela-sela banjir seremoni itu terselip berita yang jauh lebih penting namun kalah ruang: pengujian RUU Perampasan Aset dan bantahan Komisi III soal surpres pergantian Kapolri. Keduanya menyangkut arsitektur penegakan hukum nasional, dan keduanya tenggelam di antara pujian untuk pelatihan tepung."]},
  {"title": "Angka Besar, Akuntabilitas Kecil",
   "summary": "Klaim kinerja ekonomi dan proyek triliunan diumumkan tanpa pertanyaan lanjutan yang memadai.",
   "body": [
     "Kanal bisnis melaporkan sektor jasa keuangan stabil dengan kredit perbankan melesat, proyek PSEL Jawa Barat senilai Rp 7,2 triliun mulai dibangun, dan penerbitan Panda Bond serta Patriot Bond yang direstui OJK. Semuanya disampaikan dalam kerangka pencapaian, hampir tanpa suara skeptis.",
     "Padahal setiap klaim itu membawa pertanyaan yang tidak diajukan. Kredit melesat ke sektor mana dan dengan kualitas aset seperti apa. Proyek pengolahan sampah menjadi energi bernilai triliunan itu dibiayai siapa dan dengan skema tarif yang menekan APBD sampai berapa lama. Instrumen utang bertema patriotik itu menutup defisit yang mana.",
     "Lini masa techbro justru menyediakan kontrapoin yang tidak muncul di ruang redaksi: retweet soal dugaan pinjaman ratusan triliun dari bank BUMN yang diduga menguap. Ketika warganet mengajukan pertanyaan yang seharusnya diajukan wartawan ekonomi, ada yang keliru dalam pembagian kerja demokrasi kita."]},
]

ytl = [{"title": v["title"], "channel": v["channel"], "link": v["url"]} for v in yt["videos"]][:5]

digest = {
  "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
  "techbro": {"tweets_total": len(tw), "contributors": contributors, "themes": themes},
  "tempo": {"count": min(total, 12), "categories": {"groups": glist}},
  "pinggir_jurang": {"themes": pinggir},
  "youtube": ytl,
}
p = f"data/digest_{day}.json"
json.dump(digest, open(f"{D}/{p}", "w"), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN {p} themes={len(themes)} tempo={min(total,12)} yt={len(ytl)}")
