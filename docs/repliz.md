# Posting Threads melalui Repliz

Integrasi ini mengirim draft teks dan seluruh balasannya sebagai satu jadwal.
Pengiriman mati secara default. Perintah tanpa `--submit` hanya menampilkan
pratinjau lokal. Tidak diperlukan API key untuk pratinjau.

## Konfigurasi akun

1. Hubungkan akun Threads di Repliz.
2. Buka **Settings → Public API** dan buat pasangan Access Key / Secret Key.
   Simpan di `.env` lokal yang diabaikan Git; jangan kirim kunci melalui chat.
   API penjadwalan memerlukan **Premium+**. API daftar akun memerlukan Standard+.
3. Tambahkan variabel berikut ke `.env` yang sudah ada. Jangan menimpa konfigurasi
   X atau model provider. Untuk checkout baru, salin `.env.example` terlebih dulu.

   ```dotenv
   REPLIZ_ACCESS_KEY=replace-locally
   REPLIZ_SECRET_KEY=replace-locally
   REPLIZ_ACCOUNT_ID=
   REPLIZ_AUTO_SCHEDULE=false
   REPLIZ_SCHEDULE_TIME=10:00
   ```

4. Jalankan dari root repository:

   ```sh
   uv run --locked techbro --env-file .env repliz accounts
   ```

   Salin `id` akun Threads yang benar dengan `isConnected: true` ke
   `REPLIZ_ACCOUNT_ID`. Output hanya mencantumkan metadata akun, bukan token.

## Pratinjau dan kirim

Gunakan draft yang sudah dihasilkan dan ditinjau di
`DATA_DIR/threads/threads_draft_YYYYMMDD.json`. Contoh berikut memakai tanggal
draft `20261008`; ganti tanggal dan waktu dengan draft dan jadwal yang diinginkan.
Waktu harus di masa depan dan menyertakan zona waktu.

```sh
uv run --locked techbro --env-file .env repliz schedule --date 20261008 --at '2026-10-09T10:00:00+07:00'
```

Periksa teks, akun tujuan, waktu UTC, dan urutan `replies`. Setelah siap,
perintah yang sama dengan **`--submit` membuat jadwal posting sungguhan**:

```sh
uv run --locked techbro --env-file .env repliz schedule --date 20261008 --at '2026-10-09T10:00:00+07:00' --submit
uv run --locked techbro --env-file .env repliz status --date 20261008
```

`scheduled` berarti Repliz menerima jadwal dan mengembalikan `scheduleId`.
Periksa hasil penerbitan di dashboard Repliz dan profil Threads setelah waktunya.
Perintah `status` membaca catatan lokal, bukan status penerbitan langsung.

Draft yang tidak ada, tanggal tidak cocok, bagian kosong, teks melebihi 500 byte
UTF-8, waktu yang lewat, atau akun terputus ditolak. Draft baru dibuat mengikuti
batas byte tersebut; teks draft lama tidak dipotong diam-diam saat dikirim.

## Otomatis setiap hari

Setelah meninjau pratinjau dan siap menerbitkan otomatis, ubah `.env`:

```dotenv
REPLIZ_AUTO_SCHEDULE=true
REPLIZ_SCHEDULE_TIME=10:00
```

`techbro --env-file .env pipeline` kemudian menjalankan lima tahap normal dan
membuat jadwal untuk draft hari tersebut, setelah seluruh tahap berhasil.
`REPLIZ_SCHEDULE_TIME` memakai Asia/Jakarta; waktu harus lebih lambat daripada
selesainya pipeline. Jika lewat, proses gagal tanpa menjadwalkan untuk besok.
Menetapkan variabel ini saja tidak memasang cron dan tidak menjalankan pipeline.

Contoh cron untuk mesin dengan zona waktu Asia/Jakarta:

```cron
0 9 * * * cd /path/to/techbro-pipeline && .venv/bin/techbro --env-file .env pipeline
```

Sesuaikan path dan zona waktu mesin. Pada systemd, tambahkan variabel Repliz
ke environment file layanan pipeline di
[panduan native](../deploy/native/README.md). Integrasi berjalan di proses
pipeline lokal; container dashboard tidak memerlukan kunci Repliz.

## Pencegahan posting dobel

Catatan berada di `DATA_DIR/repliz/`, satu per akun dan tanggal draft. Pengiriman
ulang dengan payload sama mengembalikan catatan yang sudah berhasil tanpa
memanggil API. Perubahan teks atau jadwal untuk hari yang sudah dicatat ditolak.
Semua runner harus memakai `DATA_DIR` yang sama; checkout dengan data terpisah
tidak berbagi perlindungan ini. Cadangkan catatan bersama data produksi.

Timeout, respons tidak jelas, atau proses terputus bisa meninggalkan status
`unknown` / `pending`. Pengiriman ulang diblokir. Periksa dashboard Repliz dan
pastikan apakah jadwal sudah ada. Jika ada, kelola jadwal itu di Repliz. Hanya
setelah memastikan tidak ada jadwal, arsipkan catatan lokal terkait ke luar
`DATA_DIR/repliz/` sebelum mencoba lagi. Jangan menghapus catatan untuk sekadar
mengatasi error. Respons error juga diperlakukan secara konservatif; kunci dan
isi respons server tidak masuk log.

## Verifikasi

```sh
uv run --locked pytest tests/test_repliz.py tests/test_pipeline.py tests/test_artifacts.py
make check
```

Tes menggunakan API tiruan dan kunci sintetis. Tes tidak menerbitkan posting
atau membuktikan bahwa langganan/kunci akun produksi sudah aktif. Demo dan
verifikasi checkout bersih menghapus seluruh konfigurasi Repliz dari environment.

Referensi resmi:
[API credentials](https://docs.repliz.com/api/install),
[daftar akun](https://docs.repliz.com/api/account/get-account),
[buat jadwal](https://docs.repliz.com/api/schedule/create-schedule), dan
[spesifikasi Threads](https://docs.repliz.com/tutorial/specification/threads).
