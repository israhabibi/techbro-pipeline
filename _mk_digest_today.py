#!/usr/bin/env python3
import json, collections, datetime, os, pathlib

BASE = pathlib.Path("/home/isra_habibi/techbro")
now = datetime.datetime.now(datetime.timezone.utc)
ymd = now.strftime("%Y%m%d")

feed = json.load(open(BASE / f"data/feed_{ymd}.json"))
tempo = json.load(open(BASE / f"data/tempo_{ymd}.json"))
yt = json.load(open(BASE / f"data/tempo_yt_{ymd}.json"))

tw = [t for t in feed["tweets"] if t.get("is_techbro_id")]
cnt = collections.Counter(t["user"] for t in tw)
contributors = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
 {"title": "Perang Distribusi API: DeepSeek, Voucher, dan Ekonomi Abuse",
  "summary": "Rilis bertahap DeepSeek lewat gateway pihak ketiga memicu perburuan kredit gratis, dan sisi gelapnya langsung terlihat.",
  "body": [
   "Sepanjang siklus pemindaian ini, @lucaxyzz mendominasi percakapan dengan rangkaian pengumuman soal DeepSeek yang mulai digelar bertahap lewat gateway yang ia kelola, lengkap dengan janji zero data retention untuk varian v4 flash. Pola komunikasinya khas era distribusi model: kanal Telegram sebagai ruang tunggu, rolling access sebagai pengendali beban, dan komunitas sebagai mesin pemasaran yang dibayar dengan akses awal, bukan uang.",
   "Yang menarik justru keluhan yang menyertainya. Ia menceritakan pembagian voucher di grup yang berujung penyalahgunaan hingga 57 akun, sebuah angka yang menegaskan bahwa insentif kredit gratis selalu mengundang industri kecil pembuat akun. Di ekosistem lokal, biaya akuisisi pengguna dan biaya abuse praktis adalah dua sisi dari mata uang yang sama, dan operator kecil menanggungnya tanpa perangkat anti-fraud sekelas penyedia besar.",
   "Implikasinya melampaui satu operator. Ketika akses model frontier menjadi komoditas yang bisa dipaketkan ulang oleh siapa saja dengan gateway dan grup Telegram, keunggulan kompetitif bergeser dari teknologi ke disiplin operasional: seberapa cepat mendeteksi abuse, seberapa jujur klaim retensi data, dan seberapa tahan margin ketika harga token pemasok berubah tanpa pemberitahuan."]},

 {"title": "Sesudah Tekbum: Membaca Siklus Gelar Sarjana dan Ilusi Karier",
  "summary": "@lynxluna membingkai booming teknologi 2010-2023 sebagai siklus ekonomi biasa yang kini sedang mengempis.",
  "body": [
   "Benang merah paling reflektif datang dari @lynxluna yang menarik garis sejarah antara era Economic Boom yang melahirkan banjir sarjana ekonomi dengan era tekbum yang melahirkan banjir sarjana komputer. Argumennya sederhana namun tajam: pilihan jurusan tidak pernah murni soal minat, melainkan respons pasar tenaga kerja terhadap sinyal upah yang sedang tinggi, dan sinyal itu punya umur.",
   "Ia menambahkan dimensi akses teknologi sebagai pembeda. Ketika kemampuan menulis kode tidak lagi menjadi pembatas karena perkakas dan model bahasa memangkas jarak masuk, nilai tukar keterampilan itu turun mengikuti hukum penawaran. Yang tersisa sebagai pembeda adalah penilaian, konteks domain, dan kemampuan menanggung tanggung jawab atas sistem yang berjalan di produksi.",
   "Dalam rangkaian yang sama ia juga menyoal nilai ekonomi seorang influencer, mempertanyakan apakah kelas yang dibawa benar-benar menambah nilai di ekonomi yang ia sebut semrawut. Digabungkan, dua utas ini membentuk kritik terhadap kultur techbro lokal yang gemar merayakan status dan gelar tanpa memeriksa apakah nilai yang diproduksi bertahan setelah siklus modal murah berakhir."]},

 {"title": "Ekonomi Kreator di Persimpangan: Payout Baru X, Bot, dan Bidding Mega KOL",
  "summary": "@MikaelDewabrata mengangkat perubahan skema payout X, banjir bot di replies, dan pergeseran mekanisme lelang proyek KOL.",
  "body": [
   "Kontributor paling produktif periode ini, @MikaelDewabrata, secara terbuka melempar pertanyaan sikap kepada pengikutnya soal sistem payout baru X, meminta alasan dan bukan sekadar suara. Pertanyaan itu relevan karena skema monetisasi platform menentukan bentuk konten yang diproduksi, dan setiap perubahan formula memaksa kreator menulis ulang strategi dalam hitungan minggu.",
   "Ia juga berulang kali menunjuk masalah kualitas ruang percakapan, dari replies yang dipenuhi bot hingga diskusi tentang perpindahan pengguna antarplatform yang katanya membawa serta toksisitasnya. Pengamatan ini penting sebagai koreksi terhadap metrik keterlibatan: angka yang naik belum tentu manusia, dan monetisasi berbasis impresi rentan membiayai lalu lintas sintetis.",
   "Pada sisi bisnis, ia menilai gelembung KOL belum pecah tetapi metode bidding proyeknya sudah berubah, dengan mega KOL dituntut ikut skema kompetitif yang lebih ketat. Ia menambahkan catatan geografis bahwa perburuan proyek masih terkonsentrasi di Jakarta, sebuah pengingat bahwa ekonomi kreator Indonesia tetap timpang secara ruang meski platformnya mengklaim tanpa batas."]},

 {"title": "Budaya Perkakas: Nix, Agen Koding, dan Estetika Developer Indonesia",
  "summary": "Perdebatan varian Nix, berkas AGENTS.md, dan pembersihan helper generik menandai selera teknis komunitas.",
  "body": [
   "@__r17x menjadi motor percakapan perkakas dengan taksonomi jenaka soal pertarungan CLI Nix antara nix murni, detsys untuk kebutuhan enterprise, dan lix, sebuah lelucon internal yang sekaligus memetakan fragmentasi nyata pada ekosistem tersebut. Humor semacam ini berfungsi sebagai penanda keanggotaan komunitas sekaligus ringkasan pilihan arsitektural yang harus diambil tim.",
   "Ia juga membagikan eksperimen mendeklarasikan aturan untuk berkas AGENTS.md dan kiriman dari pengguna Codex, menandakan bahwa agen koding kini diperlakukan sebagai anggota tim yang perlu diberi kontrak tertulis. Pergeseran ini halus tetapi signifikan: dokumentasi tidak lagi hanya untuk manusia yang bergabung, melainkan untuk model yang akan mengubah basis kode.",
   "Diskusi teknis lanjutan dengan @hanipcode soal membersihkan helper yang terlalu generik seperti stringAt dan isRecord, serta catatan @hasgardians tentang penggunaan perkakas yang agnostik bahasa untuk Swift, memperlihatkan komunitas yang bergerak dari sekadar mengadopsi tren menuju perdebatan soal kebersihan abstraksi. Itu pertanda kematangan yang jarang terekam di luar lini masa."]},

 {"title": "Kirim Dulu, Ribut Kemudian: Produk Indie dan Utang Budaya Berbagi Ilmu",
  "summary": "Peluncuran produk kecil berjalan beriringan dengan kritik keras soal minimnya kultur saling menolong.",
  "body": [
   "@_kresnasatya merilis Gladion, aplikasi web untuk memonitor situs, setelah sebelumnya menggoda peluncuran produk freemium bertanggal simbolis. Ia juga transparan bahwa naskah pemasarannya dibantu AI, sebuah kejujuran kecil yang menormalkan praktik yang sudah umum tetapi jarang diakui, sekaligus menunjukkan bahwa pembuat solo kini bersaing dengan modal waktu, bukan modal tim.",
   "Nada berbeda datang dari @itsTimWijaya yang melontarkan kritik tajam bahwa orang Indonesia jarang berbagi ilmu dan saling menolong, dibingkai lewat perbandingan dengan pengalaman makan malam bersama para pendiri di San Francisco. Klaim ini provokatif dan bisa diperdebatkan, tetapi ia menyentuh keluhan lama soal ekosistem yang kompetitif secara individual namun lemah dalam infrastruktur pengetahuan bersama.",
   "@arjunaskykok menambahkan sudut pragmatis dengan membela penggunaan AI oleh restoran bermargin tipis untuk menekan biaya, sembari menyindir bahwa pengkritiknya tak pernah menjalankan bisnis restoran. Ketiga suara ini menggambarkan ketegangan yang sehat antara idealisme berbagi, realitas margin usaha, dan dorongan untuk terus meluncurkan sesuatu meski kecil."]},
]

pinggir = [
 {"title": "Transisi Energi yang Menggusur: Penolakan Geothermal Flores",
  "summary": "Penolakan Uskup Agung Ende atas proyek panas bumi menelanjangi klaim energi bersih yang mengabaikan persetujuan warga.",
  "body": [
   "Di tengah arus berita yang merayakan lonjakan penjualan kendaraan listrik dan penyerapan listrik dari pengolahan sampah, muncul satu judul yang menolak ikut paduan suara: Uskup Agung Ende menolak proyek geothermal di Flores. Penolakan dari otoritas moral setempat bukan penolakan teknis terhadap panas bumi, melainkan penolakan terhadap cara proyek dipaksakan tanpa ruang persetujuan yang bermakna bagi komunitas yang menanggung risikonya.",
   "Narasi resmi transisi energi cenderung menghitung megawatt dan target bauran, sementara biaya sosial ditulis sebagai catatan kaki. Padahal di Flores, tanah dan sumber air adalah basis penghidupan yang tidak punya pasar pengganti. Ketika negara dan investor menyebut proyek ini hijau, pertanyaan yang belum dijawab adalah hijau menurut neraca siapa dan ditanggung oleh siapa.",
   "Pola serupa terbaca pada berita penyegelan videotron setelah sepuluh pohon ditebang di Bandung dan proyek pengolahan sampah bernilai triliunan yang mulai dibangun di Jawa Barat. Pembangunan selalu datang dengan janji efisiensi, tetapi mekanisme pengawasan dan pemulihannya nyaris selalu tertinggal di belakang seremoni peletakan batu pertama."]},

 {"title": "Beban yang Dipindahkan: Komisi Ojol, BPJS, dan Utang Daerah",
  "summary": "Penyesuaian bisnis akibat aturan komisi ojol dan kanal utang baru daerah menempatkan risiko pada pihak paling lemah.",
  "body": [
   "GoTo mengungkap penyesuaian bisnis mobilitas sebagai efek aturan komisi ojol, sebuah kalimat korporat yang menyembunyikan pertanyaan konkret: siapa yang akhirnya menanggung selisihnya. Ketika platform diminta memangkas potongan, opsi yang tersedia adalah menaikkan tarif konsumen, mengurangi insentif pengemudi, atau menipiskan laba. Sejarah industri ini menunjukkan opsi ketiga paling jarang dipilih.",
   "Di jalur yang berbeda, percakapan publik soal potongan gaji dan keributan seputar BPJS yang ikut menggema di lini masa techbro memperlihatkan erosi kepercayaan terhadap skema jaminan sosial. Percepatan klaim elektronik terintegrasi memang menjanjikan efisiensi administratif, tetapi efisiensi sistem tidak otomatis berarti keadilan bagi peserta yang merasa membayar lebih banyak untuk layanan yang sama.",
   "Yang paling perlu diawasi adalah normalisasi utang. Kanal video Tempo mengangkat cara baru pemerintah daerah berutang, sementara OJK membahas penerbitan Panda Bond dan Patriot Bond. Instrumen keuangan baru selalu dijual sebagai inovasi pembiayaan pembangunan, padahal ia memindahkan tagihan ke masa depan, ke pemerintahan berikutnya, dan pada akhirnya ke warga yang tidak pernah diajak berunding."]},
]

CATMAP = {"tempo:nasional": "Nasional", "tempo:bisnis": "Bisnis", "tempo:tekno": "Tekno"}
groups, total = [], 0
for src, label in CATMAP.items():
    arts = [{"title": a["title"], "link": a["link"], "source": a["source"]}
            for a in tempo["articles"] if a["source"] == src][:3]
    if arts:
        groups.append({"category": label, "articles": arts})
        total += len(arts)

youtube = [{"title": v["title"], "channel": v["channel"], "link": v["url"]}
           for v in yt["videos"]][:5]

digest = {
  "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
  "techbro": {"tweets_total": len(tw), "contributors": contributors, "themes": themes},
  "tempo": {"count": min(total, 12), "categories": {"groups": groups}},
  "pinggir_jurang": {"themes": pinggir},
  "youtube": youtube,
}

out = BASE / f"data/digest_{ymd}.json"
out.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"DIGEST_WRITTEN data/digest_{ymd}.json themes={len(themes)} tempo={min(total,12)} yt={len(youtube)}")
