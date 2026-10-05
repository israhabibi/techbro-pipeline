# Native VPS deployment (1 vCPU / 1 GB RAM)

This runs the web app and daily pipeline directly on the host: one Uvicorn
worker, systemd, JSON files, and Caddy for HTTPS + password protection. No
Docker daemon, database, or 9router is needed for this app.

## Install on a fresh Ubuntu VPS

1. Install Python 3.11+, `python3-venv`, `ffmpeg`, `espeak-ng`, `fonts-dejavu-core`, and Caddy. Create a `techbro-data`
   group, a `techbro` system user for the scanner, and a separate `techbro-web`
   system user for the read-only web app. Place this repository at
   `/opt/techbro-pipeline`, owned by root and readable/traversable by
   `techbro-data`. Make `data/` and `dataset/` owned by `techbro:techbro-data`
   and group-writable (directories mode `2770`). The web service is sandboxed
   read-only except for `/data/videos`, where it stores generated output. It
   cannot read the scanner's X credentials.
   Create `/opt/techbro-pipeline/data/videos` as
   `techbro-web:techbro-data`, mode `2770`, before starting the web service.
2. As root, create the venv and install the web dependencies:

   ```sh
   cd /opt/techbro-pipeline
   python3 -m venv .venv
   .venv/bin/pip install -r web/requirements.txt
   ```

3. Create `/etc/techbro/techbro.env` (root-owned, mode `600`) with:

   ```ini
   ADACODE_API_KEY=your-key
   CREDS_FILE=/etc/techbro/creds.json
   SCAN_PAGES=3
   # Optional; if omitted, generated scenes use local motion cards.
   PEXELS_API_KEY=your-pexels-api-key
   ```

   Put the X credentials JSON at `/etc/techbro/creds.json`, owned by `techbro`
   and mode `600` so the scanner can read it. Make `/etc/techbro` traversable by
   that service account (for example, `root:techbro` mode `750`). Do not commit
   either file. systemd passes these values only
   to both processes, but the web account cannot read the X credentials file.

4. Install `techbro-web.service`, `techbro-daily.service`, and
   `techbro-daily.timer` into `/etc/systemd/system/`. Copy
   `Caddyfile.example` to `/etc/caddy/Caddyfile`, replace the password hash
   placeholder with the output of `caddy hash-password`, then validate Caddy's
   config before starting it. The basic-auth gate is intentional: the archive
   is derived from a personal X timeline.
5. Enable `techbro-web.service` and `techbro-daily.timer`, then enable/reload
   Caddy. Verify with `systemctl status`, `journalctl -u techbro-web`, and
   `curl -I https://airflow.my.id/daily` (expect `401` without credentials).
6. Run the first scan manually with `systemctl start techbro-daily.service`.
   Check its logs before relying on the timer.

The daily job runs at 09:00 Asia/Jakarta and scans first, then generates topics,
Threads drafts, and CSV data. The UI binds only to loopback; Caddy is the sole
public entry point. Back up `/opt/techbro-pipeline/data` and keep secrets out of
the repository. On a 1 GB host, leave swap enabled as an OOM safety net.

Video rendering is on-demand so it cannot compete with the daily scan: export
the plan or use **Generate video otomatis** in the UI. The button creates an
Indonesian voice-over locally with eSpeak NG, uses Pexels clips if an API key is
configured (otherwise it creates motion cards), burns subtitles, and returns
an MP4 plus subtitle/credit sidecars. TTS voice is intentionally local; eSpeak
is compact but noticeably synthetic. The Pexels API key is optional; its API
requires authorization and attribution links/photographer credit, which the UI
and generated credits file provide. Review the selected clip and final video
before publishing.

For the separate manual-asset workflow, export a plan, create the voice track
with another TTS tool, download reviewed clips as `scene-01.mp4`, `scene-02.mp4`,
etc., then run:

```sh
python3 render_video.py --plan video-plan-YYYYMMDD.json \
  --assets-dir ./video-assets --audio ./narration.mp3 \
  --output ./techbro-YYYYMMDD.mp4
```

The renderer refuses unreviewed or unattributed assets, outputs a vertical
1080×1920 H.264/AAC MP4 with estimated-timing subtitles, and writes a credits
sidecar. Subtitle timing is approximate, so review and adjust it in an editor.

If this hostname already uses a reverse proxy on ports 80/443 (for example,
the existing Traefik instance), do not start Caddy alongside it. Keep one
ingress only and configure that existing proxy to send traffic to
`127.0.0.1:8000` with equivalent basic authentication.
