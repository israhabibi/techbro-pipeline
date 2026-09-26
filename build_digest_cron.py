import json, collections, datetime, os

os.chdir('/home/isra_habibi/techbro')
now = datetime.datetime.now(datetime.timezone.utc)
d = now.strftime('%Y%m%d')

feed = json.load(open(f'data/feed_{d}.json'))
tempo = json.load(open(f'data/tempo_{d}.json'))
yt = json.load(open(f'data/tempo_yt_{d}.json'))

tweets = feed['tweets']
cnt = collections.Counter(t['user'] for t in tweets)
contributors = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
 {"title": "Gaji, Kurs, dan Migrasi Talenta Digital",
  "summary": "Perbandingan gaji Jakarta vs Singapura kembali jadi pemantik debat panjang di lini masa techbro Indonesia.",
  "body": [
   "Percakapan hari ini dibuka oleh @lucaxyzz yang membandingkan harga barang harian di Singapura dengan Jakarta, lalu menyimpulkan bahwa persoalan sebenarnya bukan sekadar median gaji nasional yang rendah, melainkan daya beli riil pekerja teknologi di ibu kota. Argumennya sederhana namun menohok: angka nominal rupiah terlihat besar sampai dikonversi ke keranjang belanja yang sama.",
   "Utas itu bersambung ke @ghozyulhaq yang mengangkat contoh gaji barista Starbucks Singapura sekitar 2.400-2.800 SGD per bulan, yang bila diukur dengan Big Mac Index setara belasan juta rupiah. Perbandingan ini memancing reaksi karena menempatkan pekerjaan layanan di luar negeri sejajar atau di atas posisi engineer menengah di Jakarta, sebuah kenyataan yang tidak nyaman bagi narasi 'talenta digital sebagai profesi premium'.",
   "@ArdyaDipta dan @ainunnajib menutup diskusi dengan nada lebih terukur, mengakui bahwa akses ke produk global dan pasar internasional tetap menjadi keunggulan yang sulit dibantah. Kesimpulan yang mengendap: keputusan bertahan atau pindah bukan semata soal angka, tetapi soal seberapa besar seorang software engineer benar-benar mencintai produk yang ia bangun."]},
 {"title": "Keamanan Rantai Pasok Perangkat Lunak Kembali Diuji",
  "summary": "Serangan supply chain terhadap ratusan paket npm memicu peringatan keras dari kalangan engineer lokal.",
  "body": [
   "@anvie meneruskan laporan yang menyebut serangan aktif pada rantai pasok npm telah mengompromikan setidaknya 868 paket dengan akumulasi lebih dari dua miliar unduhan bulanan. Skala ini menempatkan insiden tersebut bukan sebagai gangguan lokal, melainkan risiko sistemik bagi hampir setiap tim yang membangun di atas ekosistem JavaScript.",
   "Bagi tim engineering di Indonesia yang mayoritas mengandalkan tumpukan Node dan React, implikasinya langsung terasa. Audit dependensi, penguncian versi, dan verifikasi integritas paket berpindah dari daftar praktik ideal menjadi kebutuhan operasional harian, terutama bagi startup dengan pipeline rilis cepat dan tanpa tim keamanan khusus.",
   "Diskusi ini beririsan dengan tren lain di lini masa, yaitu meningkatnya minat pada pendekatan yang mengedepankan jaminan tipe dan verifikasi di tingkat compiler. Beberapa engineer menyebutnya sebagai reaksi wajar terhadap kelelahan menghadapi kerapuhan ekosistem paket yang terlalu bergantung pada kepercayaan."]},
 {"title": "Adopsi Effect dan Gelombang Type-Safety",
  "summary": "Pustaka Effect serta pendekatan berbasis compiler menjadi obsesi teknis sebagian besar developer aktif hari ini.",
  "body": [
   "@__r17x mendominasi percakapan teknis dengan serangkaian catatan tentang Effect, mulai dari pengamatan bahwa pustaka tersebut kini muncul di mana-mana hingga kekecewaan ringan ketika versi resmi sebuah integrasi dirilis beberapa bulan setelah ia membangun implementasinya sendiri. Pengalaman ini akrab bagi banyak developer yang bekerja di depan kurva adopsi.",
   "Tema berulang dalam utas-utas tersebut adalah keinginan membiarkan compiler membuktikan kebenaran program alih-alih mengandalkan pengujian manual. Pergeseran ini menandai kematangan komunitas lokal yang semakin nyaman dengan konsep pemrograman fungsional yang beberapa tahun lalu masih dianggap terlalu akademis.",
   "Di sisi lain, percakapan tentang perkakas harian tetap hidup, termasuk pertukaran ringan seputar Neovim dan alur kerja editor. Kombinasi antara ketelitian arsitektural dan keakraban budaya perkakas inilah yang membentuk identitas kelompok engineer paling vokal di lini masa hari ini."]},
 {"title": "AI, Infrastruktur Komputasi, dan Ekonomi Baru",
  "summary": "Dari satelit komputasi SpaceX-Nvidia hingga tenaga penjual GPU, AI meresap ke percakapan karier.",
  "body": [
   "@girikuncoro menyoroti kemitraan SpaceX dan Nvidia untuk merancang muatan komputasi AI pada satelit Starmind. Bagi komunitas teknologi Indonesia, kabar ini terbaca sebagai penanda bahwa perlombaan infrastruktur AI telah bergerak ke orbit, jauh melampaui perdebatan tentang kapasitas pusat data domestik.",
   "Pada level yang jauh lebih membumi, @lucaxyzz melontarkan pengamatan tajam tentang lulusan teknik kimia yang kini bekerja sebagai tenaga penjual GPU H200. Satu kalimat itu merangkum bagaimana permintaan perangkat keras AI menciptakan jalur karier baru yang sama sekali tidak berhubungan dengan latar belakang pendidikan formal.",
   "Dinamika serupa muncul dalam catatan @MikaelDewabrata tentang para spesialis KOL yang mulai melirik Threads meski volumenya belum menyamai Instagram, TikTok, atau YouTube. Ekonomi perhatian dan ekonomi komputasi bergerak dalam logika yang sama: modal mengalir lebih cepat daripada kesiapan sumber daya manusia."]},
 {"title": "Industrialisasi versus Kultus Startup",
  "summary": "Kritik terhadap glorifikasi kewirausahaan mengemuka, menuntut pergeseran ke industri formal.",
  "body": [
   "@lynxluna meneruskan argumen bahwa solusi bagi struktur ekonomi Indonesia adalah lebih banyak pabrik dan industri formal, bukan tambahan startup dan semangat kewirausahaan. Posisi ini menantang narasi dominan satu dekade terakhir yang menempatkan pendirian perusahaan rintisan sebagai jawaban atas persoalan lapangan kerja.",
   "Argumen pendukungnya menyebut bahwa Indonesia telah kelebihan usaha berskala kecil yang rapuh, dengan produktivitas rendah dan tanpa jaminan sosial bagi pekerjanya. Industri formal menawarkan kontrak kerja, jenjang karier, dan skala yang memungkinkan peningkatan produktivitas secara agregat.",
   "Percakapan ini menyentuh titik sensitif karena banyak anggota komunitas techbro sendiri merupakan produk dari ekosistem startup. Ketegangan antara pengalaman personal dan kesimpulan struktural inilah yang membuat utas semacam ini terus berputar tanpa titik temu yang jelas."]},
]

# Tempo
arts = tempo['articles']
bysrc = collections.OrderedDict()
for a in arts:
    bysrc.setdefault(a['source'], []).append(a)
groups = []
total = 0
for src, items in bysrc.items():
    cat = src.split(':')[-1].capitalize()
    sel = items[:3]
    total += len(sel)
    groups.append({"category": cat, "articles": [
        {"title": a['title'], "link": a['link'], "source": a['source']} for a in sel]})

pinggir = [
 {"title": "Independensi Bank Indonesia di Bawah Tekanan",
  "summary": "Redaksi Tempo menyoroti rapuhnya otonomi bank sentral saat tekanan politik fiskal menguat.",
  "body": [
   "Opini Tempo yang tayang hari ini menempatkan independensi Bank Indonesia sebagai persoalan yang tidak lagi teoretis. Ketika otoritas moneter dinilai mulai menyesuaikan langkah dengan kebutuhan pembiayaan pemerintah, garis pemisah antara kebijakan moneter dan agenda fiskal menjadi kabur, dan pasar adalah pihak pertama yang membaca perubahan itu.",
   "Sinyal ketegangan itu terlihat pula di lini masa, ketika sebuah cuitan yang dibagikan @ArdyaDipta menyebut bahwa pelaku pasar justru lebih mempercayai pernyataan Gubernur BI ketimbang pernyataan presiden. Kepercayaan pasar adalah aset yang dibangun bertahun-tahun dan dapat hilang dalam hitungan pekan.",
   "Di sisi lain, pemberitaan resmi tetap menampilkan wajah stabil: sektor jasa keuangan disebut kokoh dan kredit perbankan melesat. Kontras antara narasi stabilitas ini dengan kekhawatiran redaksional tentang tata kelola bank sentral adalah celah yang layak terus diawasi publik."]},
 {"title": "Digitalisasi Layanan Publik dan Janji yang Belum Terbukti",
  "summary": "Klaim Identitas Kependudukan Digital sebagai game changer perlu diuji dengan ukuran manfaat nyata.",
  "body": [
   "Sejumlah pemberitaan hari ini mengangkat penguatan Satu Data antara BPS dan Dukcapil, dengan Identitas Kependudukan Digital disebut sebagai game changer. Pejabat yang dikutip pun mengakui bahwa transformasi digital pelayanan publik tidak cukup hanya mengandalkan teknologi, sebuah pengakuan yang justru menunjukkan besarnya pekerjaan kelembagaan yang tersisa.",
   "Persoalan yang jarang dibahas adalah tata kelola data itu sendiri. Integrasi basis data kependudukan berskala nasional memusatkan risiko privasi pada satu titik, sementara rekam jejak perlindungan data di sektor publik belum meyakinkan. Aktivasi massal tanpa audit keamanan independen berpotensi memindahkan beban risiko kepada warga.",
   "Ironi tambahan muncul ketika pada saat yang sama komunitas teknologi membahas serangan rantai pasok yang melumpuhkan ratusan pustaka perangkat lunak global. Sistem publik dibangun di atas fondasi yang sama, dan klaim keunggulan sebaiknya diiringi transparansi mengenai bagaimana fondasi itu diamankan."]},
]

digest = {
  "generated_at": now.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
  "techbro": {"tweets_total": len(tweets), "contributors": contributors, "themes": themes},
  "tempo": {"count": min(total, 12), "categories": {"groups": groups}},
  "pinggir_jurang": {"themes": pinggir},
  "youtube": [{"title": v['title'], "channel": v['channel'], "link": v['url']} for v in yt['videos'][:5]],
}

out = f'data/digest_{d}.json'
json.dump(digest, open(out, 'w'), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN {out} themes={len(themes)} tempo={digest['tempo']['count']} yt={len(digest['youtube'])}")
