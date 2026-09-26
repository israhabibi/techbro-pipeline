# Techbro Twitter Indonesia Dataset (akumulasi semua waktu)

Kumpulan tweet dari komunitas "techbro" Indonesia (engineer/developer/founder
teknologi Tanah Air) yang dikumpulkan harian lewat timeline X (Twitter).

## Files
- `techbro_tweets.csv` — 2026 tweet techbro (akumulasi semua waktu), 1 baris per tweet, kolom:
  - `tweet_id`, `day`, `user_handle`, `text`, `created_at`, `user_score`, `reasons`
- `techbro_activity.csv` — 367 baris (1 per hari × user), kolom:
  - `day`, `user_handle`, `tweet_count`, `max_score`, `sample_texts`
- `techbro_topics.csv` — 0 topik hangat teragregasi (14 hari terakhir), kolom:
  - `topic`, `tweet_count`, `summary`, `handles`, `days`

## Method
Tweet diklasifikasi sebagai "techbro ID" lewat aturan: reference handle + lokasi
Indonesia + keyword teknologi (engineer/developer/founder/cto/dll). Topik diekstrak
dan diagregasi pakai model AI (Claude via adaCODE) dari teks tweet.

## Notes
- Data publik dari X (Twitter). Handle adalah akun publik.
- Dibuat untuk riset NLP/sosiolinguistik komunitas tech Indonesia.
- Tidak ada konten pribadi di luar apa yang sudah publik di X.
