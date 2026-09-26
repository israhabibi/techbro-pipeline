import json, collections, datetime, os

os.chdir('/home/isra_habibi/techbro')
now = datetime.datetime.now(datetime.timezone.utc)
day = now.strftime('%Y%m%d')

feed = json.load(open(f'data/feed_{day}.json'))
tb = [t for t in feed['tweets'] if t.get('is_techbro_id')]
cnt = collections.Counter(t['user'] for t in tb)
contrib = [{"user": u, "count": c} for u, c in cnt.most_common(8)]

themes = [
 {"title": "Guncangan di Puncak Google dan Kegelisahan Talenta AI",
  "summary": "Kabar mundurnya Demis Hassabis dari DeepMind serta keluarnya Jeff Dean menjadi obrolan paling panas di lini masa techbro Indonesia hari ini.",
  "body": [
   "Hari ini lini masa techbro Indonesia praktis dikuasai satu berita: guncangan di jajaran puncak Google. Kabar bahwa Demis Hassabis didepak dari kursi CEO DeepMind, disusul keluarnya Jeff Dean dan Sanjay Ghemawat untuk membangun laboratorium baru, dibagikan berulang kali oleh akun-akun yang biasanya berhati-hati soal rumor industri. @ainunnajib menyebutnya 'sangat mengejutkan', menegaskan bahwa yang pergi adalah manusia-manusia legenda di balik perusahaan teknologi tercanggih di dunia.",
   "Yang menarik bukan sekadar gosip korporatnya, melainkan cara komunitas lokal membacanya sebagai sinyal. Bagi banyak engineer di Jakarta dan Bandung, Google selama satu dekade terakhir adalah patokan stabilitas institusional: tempat riset jangka panjang bisa hidup tanpa tekanan kuartalan. Ketika arsitek intinya justru memilih keluar dan mendirikan neolab, asumsi itu ikut goyah. Beberapa akun langsung mengaitkannya dengan pertanyaan lebih besar soal siapa sebenarnya yang akan mengontrol arah pengembangan model frontier lima tahun ke depan.",
   "Nada percakapannya sendiri terbelah antara kagum dan waswas. Di satu sisi ada optimisme khas Silicon Valley yang diamplifikasi lewat retweet Sam Altman soal memilih jadi optimis dan bekerja keras ketimbang pesimis yang sibuk menjelaskan kenapa sesuatu tidak akan berhasil. Di sisi lain muncul kalimat getir bahwa masa depan datang terlalu cepat, lebih cepat dan lebih keras. Dua sentimen itu hidup berdampingan di akun yang sama, dan itulah potret jujur mood komunitas hari ini."]},
 {"title": "Vibecoding Naik Kelas: Antara Ejekan dan Permintaan Kelas Belajar",
  "summary": "Perdebatan soal vibecoder menghangat, dari sindiran developer senior sampai permintaan tulus agar komunitas IT membuka lebih banyak ruang belajar.",
  "body": [
   "Istilah vibecoding sudah lama jadi bahan candaan, tapi hari ini ia bergeser menjadi percakapan yang lebih serius. @petrabarus membuka diskusi dengan pertanyaan langsung: sebenarnya tantangan terbesar para vibecoder itu apa saja? Ia menyodorkan daftar dugaan mulai dari memahami metrik produk hingga memastikan hasil kerja benar-benar bisa dipakai, dan pertanyaan itu ditanggapi cukup ramai sebagai undangan berdialog, bukan sebagai jebakan.",
   "Balasan paling menyentuh datang dari @dhanyindraswara yang meminta para suhu IT mengadakan lebih banyak event untuk vibecoder, dengan alasan sederhana: mereka ingin belajar tapi tidak tahu apa yang sebenarnya belum mereka ketahui. Kalimat itu menelanjangi persoalan struktural yang jarang diakui, yaitu bahwa gelombang pengguna AI coding tools tumbuh jauh lebih cepat daripada infrastruktur mentoring yang tersedia untuk mereka.",
   "Di kutub sebaliknya, para praktisi tetap memamerkan disiplin teknis sebagai pembeda. @__r17x membagikan alur kerja yang jauh dari asal-asalan, mulai dari meminta agen mereview pekerjaannya sendiri lewat dokumen design thinking sampai memodelkan intent sebagai graph sebelum dieksekusi. Ia bahkan menulis dialog satir antara compiler dan AI yang saling memaki, sebuah lelucon yang sebetulnya argumen: alat boleh pintar, tapi umpan balik keras dari sistem tetap guru terbaik."]},
 {"title": "Upah Engineer Indonesia dan Luka Lama Perbandingan Regional",
  "summary": "Satu twit soal barista Starbucks Singapura yang bergaji lebih tinggi dari software engineer Jakarta kembali membuka luka lama industri.",
  "body": [
   "@itsTimWijaya melempar kalimat yang langsung terasa seperti tamparan: gaji di Indonesia begitu rendah sampai barista Starbucks di Singapura pun berpenghasilan lebih besar daripada software engineer di Jakarta. Perbandingan semacam ini bukan hal baru, tetapi tiap kali muncul ia selalu berhasil memantik reaksi karena menyentuh sesuatu yang dirasakan banyak orang secara personal, bukan sekadar statistik makro.",
   "Percakapan berlanjut ke wilayah biaya hidup dan struktur ekonomi. @ainunnajib misalnya membandingkan harga layanan di Changi dan ruang publik Singapura yang justru jauh lebih murah ketimbang di Indonesia, sebuah anomali yang membuat argumen 'gaji kecil tapi hidup murah' semakin sulit dipertahankan. Ia juga menyinggung dugaan bahwa margin usaha di dalam negeri tergerus pajak dan pungutan, baik yang resmi maupun yang tidak pernah tercatat di mana pun.",
   "Yang tersirat dari benang percakapan ini adalah kelelahan kolektif. Komunitas teknologi Indonesia sedang diminta bersaing dengan standar global dalam hal keterampilan, tetapi dihargai dengan standar lokal yang stagnan. Tidak ada yang menawarkan solusi konkret hari ini, dan justru ketiadaan solusi itulah yang membuat topik ini terus berulang setiap beberapa bulan tanpa pernah benar-benar selesai."]},
 {"title": "Ekonomi Kreator, Afiliasi, dan Realitas Kerja Digital",
  "summary": "Diskusi soal TikTok Shop, program afiliasi, dan sertifikasi magang menyingkap sisi kurang glamor dari ekonomi digital Indonesia.",
  "body": [
   "@MikaelDewabrata menjadi suara paling konsisten dalam tema ini sepanjang hari. Ia bercerita mulai menggarap TikTok GO dengan hasil yang lumayan dan membuka tawaran kerja sama bagi pemilik bisnis makanan maupun toko. Nada ceritanya membumi, jauh dari retorika growth hacking, dan justru karena itu lebih banyak orang merasa terwakili.",
   "Ia juga melontarkan kritik tajam terhadap skema afiliasi. Menurutnya seorang afiliator pada dasarnya adalah salesperson, tetapi dengan perlakuan yang jauh lebih buruk: pekerja kantoran di posisi sales setidaknya menerima gaji tetap, sedangkan afiliator paling banter mendapat fee dari transaksi yang berhasil. Pengamatan sederhana ini menyentuh perdebatan yang jauh lebih besar soal bagaimana platform memindahkan risiko ke individu sambil menjualnya sebagai kemerdekaan.",
   "Cerita personalnya soal wawancara kerja berbahasa Inggris yang berantakan pada 2009 dan berujung penolakan melengkapi gambaran tersebut. Ada pengakuan bahwa sertifikasi magang memang bukan bukti kompetensi penuh, melainkan sekadar penanda keikutsertaan seperti kursus lain. Kejujuran semacam ini terasa menyegarkan di tengah lini masa yang biasanya hanya menampilkan versi kemenangan dari setiap perjalanan karier."]},
 {"title": "Rutinitas Sunyi: Kegagalan Infrastruktur, Nostalgia Game, dan Solidaritas Kecil",
  "summary": "Di luar isu besar, komunitas mengisi hari dengan kuis infra, nostalgia Resident Evil, dan peringatan agar sesama blogger membackup kontennya.",
  "body": [
   "Tidak semua percakapan hari ini berbobot industri. @lynxluna menutup sesi kuis infrastruktur dan IT operations yang ia gelar beberapa hari terakhir, sebuah format sederhana yang efektif memancing praktisi berbagi pengalaman lapangan. Di sela itu ia juga membagikan sesi Resident Evil HD Remaster mode sulit, pengingat bahwa komunitas ini tetap manusia dengan waktu luang dan selera nostalgia.",
   "Nada solidaritas muncul dari @eLAmaravati yang mengimbau teman-teman blogger pembeli templatenya untuk segera membackup konten selagi ia masih menjadi admin. Peringatan teknis kecil semacam ini jarang viral, tapi justru menunjukkan etika komunitas yang sehat: memberi tahu lebih awal sebelum sesuatu benar-benar hilang. @digimushrm melengkapi dengan cerita soal latihan menulis blog untuk mengasah kemampuan bercerita.",
   "Ada pula momen duka yang menyatukan lintas kalangan, ketika @susipudjiastuti menyampaikan kabar kehilangan dan mendapat ucapan belasungkawa dari berbagai akun termasuk @fadlizon. @ArdyaDipta menambahkan catatan getir soal pasien BPJS yang sudah meninggal namun masih dihujat orang di internet, sebuah pengingat bahwa lini masa yang sama bisa menampung empati dan kekejaman dalam jarak beberapa scroll saja."]},
]

tempo = json.load(open(f'data/tempo_{day}.json'))['articles']
label = {'tempo:nasional': 'Nasional', 'tempo:bisnis': 'Bisnis', 'tempo:tekno': 'Tekno'}
groups, total = [], 0
for src in ['tempo:nasional', 'tempo:bisnis', 'tempo:tekno']:
    arts = [{"title": a['title'], "link": a['link'], "source": label[src]}
            for a in tempo if a['source'] == src][:3]
    total += len(arts)
    groups.append({"category": label[src], "articles": arts})

pinggir = [
 {"title": "Stabilitas yang Dipertontonkan, Kritik yang Diperkecil",
  "summary": "Narasi sinergi aparat dan capaian program pemerintah mendominasi kanal arus utama, sementara suara yang mempertanyakan biayanya nyaris tak mendapat panggung.",
  "body": [
   "Bila dibaca berurutan, keluaran kanal arus utama hari ini membentuk pola yang sulit disebut kebetulan. Ada narasi sinergi TNI, Polri, dan Kejaksaan untuk menjaga stabilitas nasional, ada rentetan keberhasilan penindakan bea cukai, dan ada rangkaian seremoni kepala daerah menandatangani nota kesepahaman. Semuanya benar sebagai peristiwa, tetapi komposisinya menghasilkan kesan tunggal: negara sedang bekerja dan tidak perlu dipersoalkan.",
   "Yang hilang dari komposisi itu adalah pertanyaan tentang ongkos. Ketika sinergi aparat dirayakan sebagai penjaga stabilitas, jarang disertai pembahasan mengenai batas kewenangan dan mekanisme akuntabilitas yang menyertainya. Stabilitas yang tidak pernah diuji oleh kritik bukanlah stabilitas yang kokoh, melainkan stabilitas yang belum diperiksa. Perbedaan keduanya baru terlihat ketika ada yang salah dan tidak ada satu pun kanal yang siap memeriksanya.",
   "Isu putusan Mahkamah Konstitusi terkait program makan bergizi gratis menjadi contoh paling jelas. Pembingkaian yang menonjol adalah penegasan bahwa putusan itu bukan perintah menghentikan program, bukan telaah atas apa sebenarnya yang dipersoalkan hakim konstitusi. Publik akhirnya menerima kesimpulan tanpa pernah diajak menimbang argumennya, dan itu bentuk pengecilan ruang kritik yang paling halus sekaligus paling efektif."]},
 {"title": "Angka Ekonomi Membaik di Atas Kertas, Getir di Lapangan",
  "summary": "Laporan kredit melesat dan IHSG menguat berdiri berseberangan dengan keluhan margin usaha yang tergerus pungutan dan penyesuaian bisnis akibat regulasi ojol.",
  "body": [
   "Kanal bisnis hari ini menyodorkan indikator yang tampak menenangkan: sektor jasa keuangan disebut stabil, kredit perbankan melesat, dan IHSG menguat tipis sepanjang pekan. Angka-angka ini valid, tetapi ia mengukur kesehatan sistem keuangan, bukan kesehatan orang yang menjalankan usaha di dalamnya. Perbedaan itu sering kabur dalam pemberitaan dan menghasilkan optimisme yang tidak dirasakan mayoritas.",
   "Di sisi lain, berita soal GoTo yang menyesuaikan bisnis mobilitas akibat kebijakan komisi ojol menunjukkan wajah lain dari ekonomi yang sama. Penyesuaian korporat selalu punya ujung yang menimpa mitra pengemudi, meski bagian itu paling jarang dilaporkan secara rinci. Demikian pula penurunan harga BBM nonsubsidi yang dijelaskan sebagai kabar baik, tanpa penelusuran memadai atas dinamika yang membuatnya mungkin.",
   "Suara paling jujur justru datang dari luar kanal resmi, dari pelaku usaha yang menyebut margin mereka tergerus pajak dan pungutan, baik yang resmi maupun yang hanya ada di realitas lapangan. Selama pengalaman semacam itu tidak masuk ke dalam laporan ekonomi arus utama, kita akan terus punya dua versi Indonesia yang tidak pernah bertemu: satu yang tumbuh di grafik, satu lagi yang bertahan di jalanan."]},
]

yt = [{"title": v['title'], "channel": v['channel'], "link": v['url']}
      for v in json.load(open(f'data/tempo_yt_{day}.json'))['videos']][:5]

digest = {
    "generated_at": now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    "techbro": {"tweets_total": len(tb), "contributors": contrib, "themes": themes},
    "tempo": {"count": min(total, 12), "categories": {"groups": groups}},
    "pinggir_jurang": {"themes": pinggir},
    "youtube": yt,
}
out = f'data/digest_{day}.json'
json.dump(digest, open(out, 'w'), ensure_ascii=False, indent=2)
print(f"DIGEST_WRITTEN {out} themes={len(themes)} tempo={digest['tempo']['count']} yt={len(yt)}")
