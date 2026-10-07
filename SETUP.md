# Setup Baru — Replicate Pipeline dari Repo Ini

Panduan buat agent/mesin lain yang mau replicate techbro pipeline dari nol.

## Prasyarat

- Linux, Python 3.11+, Docker + Docker Compose
- Node ≥18 (buat MCP, optional)
- Akses: X session cookies (creds.json), adaCODE API key, Kaggle token

## 1. Install dependencies Python

```bash
python3 -m venv .venv
.venv/bin/pip install httpx requests twikit psycopg2-binary fastapi 'uvicorn[standard]' jinja2 kaggle
```

(versi yang teruji ada di `web/requirements.txt` untuk web; sisanya versi bebas)

## 2. Secrets (TIDAK ada di repo — wajib disiapkan sendiri)

```bash
cp .env.example .env   # isi ADACODE_API_KEY, KAGGLE_API_TOKEN
# creds.json (X session) — export dari browser:
#   DevTools → Application → Cookies → https://x.com
#   butuh: auth_token, ct0, twid, kdt, bearer
#   format: {"auth_token":"...","ct0":"...","twid":"...","kdt":"...","bearer":"..."}
```

⚠️ `creds.json` expired bila X auto-logout. Gejala: scan.py dapat 0 tweet / 401.

## 3. Alur pipeline (urutan eksekusi)

`pipeline_daily.sh` menjalankan semua ini berurutan (5 tahap):

1. **`scan.py`** — fetch X home timeline (pakai creds.json cookie) → `data/feed/feed_YYYYMMDD.json`
2. **`sources.py`** — Google News + Tempo RSS → `data/sources/sources_YYYYMMDD.json`
3. **`topic_tracker.py`** — ekstrak brief topik 24 jam (1 call adaCODE) → `data/topics/topics_YYYYMMDD.json`
4. **`build_threads_draft.py`** — draft Threads dari topik → `data/threads/threads_draft_YYYYMMDD.{json,txt}`
5. **`build_dataset.py`** — rebuild CSV dataset → `dataset/*.csv` (buat Kaggle)

> Step `merge_sources.py` + `build_digest_cron.py` sudah dihapus. Keduanya bergantung
> pada `digest_YYYYMMDD.json` yang tidak pernah dibuat cron mana pun. Chat di web
> sekarang membaca langsung dari `topics_` + `feed_` + `sources_`.

## 4. Web

```bash
docker compose up -d --build digest
# serve di port 8000, reverse proxy via traefik (lihat dynamic.yml router digest-domain)
```

Route: `/` arsip harian · `/status` health check pipeline · `/topics-timeline` tren topik

## 5. Cron

Pipeline HARUS di-trigger dari luar (tidak self-scheduling):
- `0 8 * * * cd /path/techbro-pipeline && ./pipeline_daily.sh >> data/pipeline.log 2>&1`
- Pipeline nulis snapshot `crontab -l` ke `data/crontab.txt` supaya `/status` bisa
  menampilkan jadwal tanpa akses ke host (container ga bisa baca crontab host).

## 6. Kaggle dataset (optional)

```bash
export KAGGLE_CONFIG_DIR=~/.kaggle
# token di .env: KAGGLE_API_TOKEN (format KGAT_ v2)
cd dataset && kaggle datasets metadata --update israhabibi/techbro-twitter-indonesia -p .
kaggle datasets create -p . --dir-mode zip   # untuk push pertama
```

## Gotchas (penting!)

- Web tokopedia/x.com/search DIBLOKIR dari IP datacenter (Akamai) — hanya home timeline via cookie yang jalan
- `scan.py` butuh cookie VALID; kalau `feed_*.json` kosong → cookie expired
- Cek `/status` kalau pipeline keliatan nggak jalan — tahap yang `[skip]` atau artifact-nya belum ada ditandai langsung di sana
- Docker image `techbro-digest` harus di-rebuild tiap ganti template/data
- Semua path `BASE = os.path.dirname(os.path.abspath(__file__))` — jalankan dari folder repo
- Jangan commit `.env` / `creds.json` / `data/` / `certs/` (udah digitignore)
