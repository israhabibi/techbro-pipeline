---
name: techbro-digest-pipeline
description: 'Maintain the Techbro pipeline on VPS: cron job, data file layout, web deploy via docker compose. Used when user says "pipeline jalan", "draft kepanjangan", "ubah format web", "buat pendek", "ilangin tempo", "status pipeline".'
---

# Techbro Pipeline

Techbro pipeline running on VPS `/home/isra/techbro/techbro-pipeline`.

Lima tahap, dipanggil berurutan oleh `pipeline_daily.sh`:
scan → sources → topic_tracker → build_threads_draft → build_dataset.

## Data Files

Semua di `data/<prefix>/<prefix>_YYYYMMDD.json`:

- `data/feed/feed_YYYYMMDD.json` — raw tweets from X timeline scan, tiap tweet udah ada flag `is_techbro_id` / `is_tech_tweet` / `user_score`
- `data/sources/sources_YYYYMMDD.json` — `{keywords: {kw: [item]}, tempo: [item]}`
- `data/topics/topics_YYYYMMDD.json` — brief editorial 24 jam. Tiap topik: `topic`, `count`, `summary`, `context`, `value_added`, `handles`, `days`
- `data/threads/threads_draft_YYYYMMDD.json` — draft Threads, `{status, parts: [{number, kind, text}]}`
- `dataset/*.csv` — Kaggle-ready

Tidak ada `digest_*.json` lagi. Step `merge_sources.py` + `build_digest_cron.py`
sudah dihapus karena keduanya bergantung pada file yang tidak pernah dibuat cron.

## Draft Format

`build_threads_draft.py` bangun dari `topics_*.json`:
1. `opening` — 1 baris konteks
2. `topic` — 4 topik teratas, tiap part ≤500 char (batas Threads), kalimat tidak
   pernah dipotong di tengah (`sentences()` pecah di `[.!?]`)
3. `closing` — pertanyaan penutup

Ranking pakai `editorial_score()`: `count * 2` + bobot keyword (`agent` +6,
`rust`/`observability` +4, `bootcamp`/`cohort` -2, `ekspektasi` -3).

## Cron

```bash
0 8 * * * cd /home/isra/techbro/techbro-pipeline && ./pipeline_daily.sh >> data/pipeline.log 2>&1
```

Pipeline nulis `crontab -l` ke `data/crontab.txt` tiap selesai run.

## Web

```bash
cd /home/isra/techbro/techbro-pipeline
docker compose up -d --build digest
```

Route: `/` arsip harian · `/status` health check · `/topics-timeline` tren topik

`/status` parse `data/pipeline.log` run terakhir + cek artifact tiap tahap.
Badge: OK / perlu perhatian / dilewati / gagal. Jalur JSON di `/api/status`.

## Pitfalls & User Preferences

- User ingin format PENDEK, bukan narasi 4-5 paragraf
- No Tempo, no politics di output — techbro only
- Filter content by topic (AI/coding/startup/engineering), NOT by `is_techbro_id` flag
- Chat AI (adaCODE) TIDAK ada di template `/`; hanya endpoint `/api/chat` terpisah
- `data/pipeline.log` append-only — parser cuma baca 512KB terakhir
- Rebuild web selalu pakai `docker compose up -d --build digest` (volume cuma mount `./data`, kode ada di image)