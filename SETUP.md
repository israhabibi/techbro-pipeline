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

`pipeline_daily.sh` menjalankan semua ini berurutan:

1. **`scan.py`** — fetch X home timeline (pakai creds.json cookie) → `data/feed_YYYYMMDD.json`
2. **`sources.py`** — Google News + RSS → `data/sources_*.json`
3. **`merge_sources.py`** — gabung feed + sources → `data/merged_*.json`
4. **`build_digest_cron.py`** — (dipanggil via cron Hermes dengan LLM) → `data/digest_YYYYMMDD.json`
   - Format digest: LIHAT `.skills/techbro-digest-pipeline/SKILL.md` (PENDEK 6 poin)
5. **`topic_tracker.py`** — update `data/topics_*.json` (window 14 hari, klasifikasi via adaCODE)
6. **`build_dataset.py`** — rebuild CSV dataset → `dataset/*.csv` (buat Kaggle)

## 4. Web digest

```bash
docker compose up -d --build digest
# serve di port 8000, reverse proxy via traefik (lihat dynamic.yml router digest-domain)
```

## 5. Cron

Pipeline HARUS di-trigger dari luar (tidak self-scheduling):
- Hermes cron: prompt generator (pake LLM) — lihat skill SKILL.md bagian Cron Job
- Atau plain crontab: `0 1 * * * cd /path/techbro && ./pipeline_daily.sh`

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
- Docker image `techbro-digest` harus di-rebuild tiap ganti template/data
- Semua path `BASE = os.path.dirname(os.path.abspath(__file__))` — jalankan dari folder repo
- Jangan commit `.env` / `creds.json` / `data/` / `certs/` (udah digitignore)
