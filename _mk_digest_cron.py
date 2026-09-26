import json, collections, datetime, os

os.chdir('/home/isra_habibi/techbro')
day = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

feed = json.load(open(f'data/feed_{day}.json'))
tweets = feed['tweets']
cnt = collections.Counter(t['user'] for t in tweets if t.get('user'))
contributors = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
 {"title": "Prompt Engineering Dinyatakan Mati, Graph Jadi Suksesornya",
  "summary": "Wacana matinya prompt engineering mendominasi lini masa techbro Indonesia hari ini, dipicu kutipan Andrew Ng soal graph sebagai pengganti prompting.",
  "body": [
   "Hari ini lini masa techbro Indonesia diramaikan kutipan pendiri Google Brain, Andrew Ng, yang menyebut prompting akan mati dalam enam bulan dan digantikan oleh pendekatan berbasis graph. Retweet dari @ArdyaDipta menyebarkan klaim itu ke lingkaran engineer lokal, sementara @ainunnajib merangkumnya dengan satu kalimat sinis yang langsung viral: prompt engineering is dead, long live prompting.",
   "Nada percakapannya bukan penolakan, melainkan kelelahan. Banyak praktisi merasa siklus hype AI berputar terlalu cepat: baru saja perusahaan merekrut posisi prompt engineer, kini kerangka kerjanya sudah dianggap usang. Yang tersisa adalah pertanyaan praktis siapa yang menanggung biaya belajar ulang, dan apakah perusahaan Indonesia punya kapasitas untuk mengikuti pergantian paradigma setahun sekali.",
   "Di sisi lain, ada nada realistis dari kalangan engineer senior yang menilai perdebatan ini lebih soal penamaan daripada substansi. Merancang konteks, menyusun struktur data, dan mengorkestrasi model tetap pekerjaan yang sama; hanya labelnya yang berganti. Konsensus tak resmi di timeline hari ini: abaikan istilahnya, kuasai fundamental sistemnya."
  ]},
 {"title": "AI Slop dan Perlawanan Kelas Kreatif",
  "summary": "Kemarahan desainer terhadap konten AI murahan meledak lewat cuitan @eLAmaravati yang diamplifikasi luas, menyorot ancaman terhadap upah pekerja kreatif.",
  "body": [
   "Cuitan @eLAmaravati dengan huruf kapital penuh, menuntut kenaikan gaji desainer dan mengecam AI slop, menjadi salah satu momen paling emosional di timeline hari ini. Poin utamanya sederhana namun tajam: kemampuan mengoperasikan Canva atau perangkat desain lain tidak otomatis menjadikan seseorang desainer, dan generator gambar tidak menggantikan penilaian estetis yang terlatih.",
   "Amplifikasi dari @MikaelDewabrata membawa perdebatan itu ke audiens yang lebih luas dan memicu diskusi soal harga jasa kreatif yang terus tertekan. Kekhawatiran yang berulang adalah klien kini menggunakan hasil AI sebagai patokan tawar-menawar, menekan tarif ke bawah tanpa memperhitungkan revisi, riset, dan tanggung jawab merek.",
   "Ironi hari ini muncul dari sisi lain: @lucaxyzz secara terbuka bercanda bahwa satu prompt baru saja mematikan pekerjaan editor videonya. Candaan itu justru merangkum ketegangan sebenarnya, di mana pengguna teknologi dan korban teknologi sering kali duduk di lingkaran pertemanan yang sama."
  ]},
 {"title": "Gelombang Studio dan Produk AI Buatan Lokal",
  "summary": "Peluncuran design studio berbasis AI dan eksperimen knowledge base menandai bahwa ekosistem lokal bergerak dari komentar ke produk.",
  "body": [
   "@lucaxyzz mengumumkan peluncuran Vantis AI, sebuah design studio yang tumbuh dari empat bulan nongkrong di kantin kantor rekannya. Kisah asal-usul yang sangat Indonesia ini mendapat sambutan hangat, sekaligus menegaskan pola bahwa banyak startup lokal lahir dari jejaring pertemanan, bukan dari akselerator formal.",
   "Di jalur berbeda, @ismailfahmi menghabiskan seharian membangun integrasi Obsidian dengan Claude untuk Himpunan Putusan Tarjih Muhammadiyah. Proyek ini menarik karena memindahkan AI dari ranah demo teknologi ke ranah pengetahuan keagamaan terstruktur, sebuah domain yang selama ini jarang disentuh eksperimen open tooling di Indonesia.",
   "Benang merahnya jelas: percakapan lokal mulai bergeser dari mengomentari rilis perusahaan Amerika menuju membangun sesuatu yang spesifik terhadap konteks Indonesia. Skalanya masih kecil dan sebagian besar berupa proyek akhir pekan, tetapi arahnya menandakan kematangan yang lebih sehat dibanding siklus hype sebelumnya."
  ]},
 {"title": "Monetisasi X dan Ekonomi Perhatian yang Meragukan",
  "summary": "Skema monetisasi baru X memicu perdebatan soal konten orisinal, nilai kontribusi, dan apakah cuitan layak dihargai uang.",
  "body": [
   "@MikaelDewabrata menyoroti syarat skema monetisasi baru yang mewajibkan pengguna menyerahkan sepuluh contoh konten orisinal. Reaksinya bercampur antara mempersiapkan diri dan mempertanyakan siapa sebenarnya yang menentukan definisi orisinal di platform yang selama ini justru menghadiahi konten daur ulang.",
   "@lucaxyzz mengambil posisi yang lebih filosofis, menyatakan bahwa ia tidak pernah memikirkan monetisasi dan memandang aktivitasnya di X sebagai kontribusi ke masyarakat. Sikap ini mendapat simpati, namun juga memancing kritik bahwa hanya mereka yang sudah mapan secara finansial yang mampu bersikap acuh terhadap monetisasi.",
   "Di baliknya tersimpan kegelisahan yang lebih besar soal ke mana perhatian komunitas teknologi Indonesia bermigrasi. Keluhan bahwa Threads menjadi makin toksik sejak gelombang perpindahan dari X menunjukkan tak ada pelabuhan yang benar-benar aman, hanya perpindahan masalah dari satu kolam ke kolam lain."
  ]},
 {"title": "Budaya Engineering dan Nostalgia Startup Tahap Awal",
  "summary": "Cerita masa awal Sayurbox dan diskusi kualitas kode menghidupkan refleksi soal budaya rekayasa perangkat lunak di Indonesia.",
  "body": [
   "Cerita @lwastuargo tentang bergabung dengan Sayurbox saat timnya masih sekitar sembilan orang, dengan budaya engineering yang ia sebut cukup lawas, memicu gelombang nostalgia di kalangan engineer senior. Cerita semacam ini berfungsi sebagai arsip informal sejarah teknologi Indonesia yang jarang terdokumentasi secara resmi.",
   "Diskusi teknis yang mengiringinya berputar pada kualitas kode, termasuk pengingat bahwa meninjau lima ribu baris fungsi murni jauh lebih ringan daripada seribu baris kode berantakan. Prinsip lama ini terasa relevan kembali di era ketika AI mampu memproduksi kode dalam volume besar dengan kualitas yang tidak selalu terjaga.",
   "Percakapan ditutup dengan nada komunitas yang khas: pertanyaan langsung soal angka pendapatan bulanan, saling dorong, dan usulan bahwa banyak persoalan sebenarnya selesai dengan lebih sering ngopi bareng. Modal sosial masih menjadi infrastruktur paling nyata di ekosistem teknologi Indonesia."
  ]},
]

arts = json.load(open(f'data/tempo_{day}.json'))['articles']
byc = collections.OrderedDict()
for a in arts:
    c = (a.get('source') or 'tempo').split(':')[-1]
    byc.setdefault(c, [])
    if len(byc[c]) < 3:
        byc[c].append({"title": a['title'], "link": a['link'], "source": a.get('source', 'Tempo')})
groups = [{"category": k, "articles": v} for k, v in byc.items()]
count = min(12, sum(len(g['articles']) for g in groups))

pinggir = [
 {"title": "Anggaran Cekak, Aparat Diliburkan: Negara Kehabisan Napas Fiskal",
  "summary": "Wacana pegawai negeri diliburkan akibat dana cekak dan ancaman krisis anggaran daerah menunjukkan kegagalan tata kelola fiskal yang ditanggung rakyat.",
  "body": [
   "Ketika pembahasan publik didominasi kabar pegawai negeri yang diliburkan karena dana cekak, yang sedang kita saksikan bukan efisiensi melainkan gejala kebangkrutan perencanaan. Anggaran daerah tidak tiba-tiba menyusut dalam semalam; ia dikeringkan oleh serangkaian keputusan pusat, transfer yang tertunda, dan program mercusuar yang diprioritaskan di atas belanja layanan dasar.",
   "Narasi resmi cenderung membingkai ini sebagai penghematan bersama, padahal beban jatuh paling keras pada lapisan terbawah birokrasi dan warga yang bergantung pada layanan mereka. Pegawai kontrak, guru honorer, dan tenaga kesehatan daerah adalah pihak pertama yang merasakan pemotongan, sementara belanja seremonial di tingkat atas jarang tersentuh audit yang setara.",
   "Pertanyaan yang seharusnya diajukan bukan berapa banyak yang bisa dihemat, melainkan mengapa ruang fiskal habis begitu cepat setelah janji pertumbuhan yang berulang kali disampaikan. Tanpa transparansi rinci soal ke mana dana mengalir, imbauan berhemat hanyalah cara halus memindahkan kegagalan negara ke pundak pegawai dan warga."
  ]},
 {"title": "BUMN, Selebritas, dan Nuklir: Politik Penunjukan Tanpa Pertanggungjawaban",
  "summary": "Masuknya figur populer ke struktur BUMN dan tarik-menarik soal penelitian nuklir BRIN memperlihatkan keputusan strategis yang dibuat tanpa deliberasi publik.",
  "body": [
   "Pembicaraan soal kehadiran figur selebritas di lingkungan perusahaan milik negara kembali membuka luka lama: jabatan strategis di BUMN masih diperlakukan sebagai mata uang politik, bukan posisi teknokratis yang menuntut rekam jejak. Setiap penunjukan semacam ini menggerus argumen bahwa BUMN dikelola atas dasar kinerja.",
   "Pada saat bersamaan, polemik seputar penelitian nuklir BRIN menunjukkan pola yang serupa dari arah berbeda. Ketika penjelasan datang dari juru bicara politik alih-alih dari otoritas ilmiah yang bertanggung jawab, publik dipaksa menilai kebijakan berisiko tinggi melalui saringan komunikasi kekuasaan, bukan melalui data dan kajian keselamatan.",
   "Dua kasus ini bertemu pada satu titik: melemahnya institusi sebagai penyaring keputusan. Selama penunjukan dan arah riset ditentukan oleh kedekatan politik, kritik akan selalu dibingkai sebagai gangguan, dan biaya kesalahan akan kembali dibayar oleh anggaran publik yang sedang sekarat."
  ]},
]

vids = json.load(open(f'data/tempo_yt_{day}.json'))['videos'][:5]
youtube = [{"title": v['title'], "channel": v.get('channel', 'tempodotco'), "link": v['url']} for v in vids]

digest = {
 "generated_at": now,
 "techbro": {"tweets_total": len(tweets), "contributors": contributors, "themes": themes},
 "tempo": {"count": count, "categories": {"groups": groups}},
 "pinggir_jurang": {"themes": pinggir},
 "youtube": youtube,
}
p = f'data/digest_{day}.json'
json.dump(digest, open(p, 'w'), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN {p} themes={len(themes)} tempo={count} yt={len(youtube)}")
