# Posting otomatis melalui Meta Threads API

Publisher resmi Meta tersedia melalui `techbro meta`. Pratinjau tidak memerlukan
token dan tidak menghubungi Meta. `--submit` menerbitkan posting sungguhan saat
perintah dijalankan. Penjadwalan dilakukan oleh cron/systemd di mesin lokal.

## Konfigurasi

Tambahkan ke `.env` lokal yang diabaikan Git, tanpa menimpa konfigurasi lain:

```dotenv
THREADS_APP_ID=your-threads-app-id
THREADS_ACCESS_TOKEN=your-threads-user-access-token
THREADS_USER_ID=
THREADS_AUTO_PUBLISH=false
REPLIZ_AUTO_SCHEDULE=false
```

Gunakan token akun pengguna Threads, dengan izin `threads_basic` dan
`threads_content_publish`. Threads app ID dan app secret berbeda dari kredensial
aplikasi Meta umum. App ID adalah identitas aplikasi; user ID adalah identitas
akun yang menerbitkan posting. Untuk perintah publisher dengan user token yang
sudah dibuat, app secret tidak diperlukan.

Untuk akun sendiri, tambahkan sebagai **Threads Tester**, terima undangan melalui
**Website permissions → Invites** di Threads, lalu gunakan **User Token Generator**
di pengaturan use case Threads. Ketentuan App Review/penerbitan aplikasi untuk
pengguna lain tetap mengikuti dashboard Meta.

Cek profil menggunakan permintaan baca saja:

```sh
uv run --locked techbro --env-file .env meta profile
```

Masukkan `id` hasilnya ke `THREADS_USER_ID`. Saat pengiriman, publisher memeriksa
bahwa token memang terhubung ke akun tersebut. Membaca profil berhasil belum
membuktikan bahwa token mempunyai izin menerbitkan posting.

## Tinjau dan kirim draft

Draft berada di `DATA_DIR/threads/threads_draft_YYYYMMDD.json`. Perintah berikut
menggunakan tanggal hari ini di Asia/Jakarta; tambahkan `--date YYYYMMDD` untuk
memilih tanggal lain secara eksplisit:

```sh
uv run --locked techbro --env-file .env meta publish
```

Periksa seluruh teks, nomor bagian, dan akun tujuan. Jika draft hari ini belum
ada, jalankan pipeline dengan `THREADS_AUTO_PUBLISH=false` terlebih dahulu:

```sh
uv run --locked techbro --env-file .env pipeline
```

Setelah siap, **`--submit` menerbitkan seluruh rangkaian sekarang**:

```sh
uv run --locked techbro --env-file .env meta publish --submit
uv run --locked techbro --env-file .env meta status
```

Publisher membuat container teks, menunggu status `FINISHED`, lalu memanggil
endpoint publish. Bagian kedua membalas posting pertama, bagian ketiga membalas
bagian kedua, dan seterusnya. Pengiriman berhenti pada kegagalan. Nomor posting
dan ID dari Meta tersimpan di catatan lokal. Periksa rangkaian pada profil Threads
sesudah pengiriman. Perintah `status` membaca catatan lokal, bukan status moderasi
atau visibilitas terbaru dari Meta.

## Otomatis setelah pipeline

Setelah meninjau hasil dan siap mengaktifkan penerbitan otomatis, ubah:

```dotenv
THREADS_AUTO_PUBLISH=true
REPLIZ_AUTO_SCHEDULE=false
```

Pipeline kemudian menerbitkan draft hanya setelah kelima tahap berhasil. Tidak
ada posting jika pengumpulan gagal. Mengaktifkan Meta dan Repliz sekaligus ditolak
sebelum pengumpulan dimulai. Menetapkan flag saja tidak memasang cron atau
menjalankan pipeline.

Contoh cron untuk mesin dengan zona waktu Asia/Jakarta:

```cron
0 9 * * * cd /path/to/techbro-pipeline && .venv/bin/techbro --env-file .env pipeline
```

Sesuaikan path dan zona waktu. Untuk systemd, tambahkan variabel ke environment
file layanan pipeline dalam [panduan native](../deploy/native/README.md). Token
Threads hanya diperlukan oleh proses pipeline/publisher; container dashboard
tidak memerlukannya.

## Melanjutkan proses yang gagal

Catatan berada di `DATA_DIR/meta/`, satu per akun dan tanggal draft. Semua runner
harus memakai `DATA_DIR` yang sama; cadangkan catatan bersama data produksi.
Menjalankan ulang draft yang sudah selesai tidak membuat posting baru. Mengubah
teks setelah proses tercatat ditolak agar rangkaian tidak tercampur.
Catatan juga menyimpan salinan draft asli. Jika pipeline berikutnya mengganti
file draft, tinjau salinan tersebut dengan `meta publish --resume --date YYYYMMDD`.
Untuk melanjutkan rangkaian asli yang hasilnya diketahui, tambahkan `--submit`
ke perintah itu; bagian yang sudah diterbitkan dilewati. `--resume` tetap memblokir
status publish yang tidak pasti, dan tidak otomatis mengirim jika tanpa `--submit`.

Jika pembuatan container gagal atau responsnya hilang, proses dapat dijalankan
ulang; container dibuat tanpa `auto_publish_text`. Posting sebelumnya yang sudah
berhasil dilewati. Container yang masih diproses diperiksa lagi pada pengiriman
ulang, dengan ID yang sama. Status container yang error/kedaluwarsa menghentikan
proses dan membutuhkan pemeriksaan.

Jika publish mengalami timeout, respons tanpa ID, atau proses terputus sebelum
menyimpan hasilnya, status `unknown`/`publishing` memblokir pengiriman ulang.
Periksa akun Threads dan catatan ID container sebelum melakukan pemulihan manual.
Jangan menghapus seluruh catatan jika beberapa bagian sudah diterbitkan: itu
dapat membuat posting sebelumnya terkirim lagi. CLI tidak otomatis menebak ID
posting yang hilang. Meta API tidak menyediakan jaminan exactly-once dari catatan
lokal ini; pengiriman dari mesin dengan data terpisah juga tidak berbagi kunci.

## Memperbarui token

Long-lived token memiliki masa berlaku 60 hari. Refresh dilakukan setelah token
berumur setidaknya 24 jam dan sebelum kedaluwarsa. Jalankan secara berkala,
misalnya setiap dua minggu:

```sh
uv run --locked techbro --env-file .env meta refresh --save-token .env
```

Perintah ini memperbarui token melalui Meta, menyimpannya ke environment file
yang dipilih dengan izin `600`, serta mempertahankan konfigurasi lain. Output
hanya menampilkan metadata masa berlaku. File tujuan harus berisi token yang
sama dengan token aktif agar file akun lain tidak tertimpa. Jika memakai token
yang diekspor langsung di shell, muat ulang nilainya setelah refresh; environment
yang diekspor memiliki prioritas atas `.env`. Token kedaluwarsa perlu dibuat ulang
melalui Meta. Refresh belum dijadwalkan otomatis oleh repo.

## Verifikasi

```sh
uv run --locked pytest tests/test_meta.py tests/test_pipeline.py
make check
uv run --locked python scripts/smoke.py
```

Tes publish/refresh memakai API tiruan dan token sintetis. Smoke test menjalankan
pratinjau paket dari luar checkout tanpa token dan tanpa posting. Verifikasi Git
bersih menghapus seluruh konfigurasi Threads dan Repliz dari environment. Tes
tersebut tidak membuktikan izin publish atau kondisi akun produksi.

Referensi resmi:
[koleksi API Meta](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api),
[contoh aplikasi Meta](https://github.com/fbsamples/threads_api), dan
[masa berlaku token](https://developers.facebook.com/docs/threads/get-started/long-lived-tokens).
