# Native Linux deployment

Prerequisites: Git, Python 3.11+, uv, FFmpeg, eSpeak NG, DejaVu fonts, systemd, and
one existing authenticated HTTPS reverse proxy (or Caddy).

1. Create a `techbro-data` group and separate `techbro` and `techbro-web` system
   accounts in that group. Clone the repository at `/opt/techbro-pipeline` and
   install as an administrator with
   `uv sync --locked --no-dev --no-editable --python /usr/bin/python3 --no-managed-python`.
   Use the system interpreter so service accounts do not depend on an
   administrator's private Python cache beneath a home directory.
2. Create `data/` and `dataset/` owned by `techbro:techbro-data`, directories mode
   `2770`. Create `data/videos/` owned by `techbro-web:techbro-data`, mode `2770`.
   Ensure the installed package and interpreter are readable by both accounts.
3. Create `/etc/techbro` as `root:techbro`, mode `750`. Put credentials at
   `/etc/techbro/creds.json`, owned by `techbro`, mode `600`. Create the protected
   environment file `/etc/techbro/techbro.env`, owned by root, mode `600`:

   ```ini
   CREDS_FILE=/etc/techbro/creds.json
   SCAN_PAGES=3
   ADACODE_API_KEY=replace-with-key
   ADACODE_MODEL=adacode-2.0
   ENABLE_SUPPLEMENTAL_RSS=1
   TTS_BACKEND=local
   ```

   Add `PEXELS_API_KEY` only if external video clips are wanted. The web account
   cannot read the scanner's credential file. Environment variables are passed
   by systemd; `.env` is not required for these services.
   For the optional [official Threads publisher](../../docs/meta-threads.md), add
   `THREADS_ACCESS_TOKEN` and the verified `THREADS_USER_ID` to this protected
   environment file. Set `THREADS_AUTO_PUBLISH=true` only when automatic posting
   at pipeline completion is wanted. Keep `REPLIZ_AUTO_SCHEDULE=false`.
4. Install the three `techbro-*.service`/`.timer` files in `/etc/systemd/system/`.
   Run `systemd-analyze verify` on them, then `systemctl daemon-reload`.
5. Configure your single ingress. `Caddyfile.example` uses HTTPS and basic auth;
   replace its domain and password-hash placeholder and run `caddy validate`.
   Keep an existing reverse proxy if one already occupies ports 80/443.
6. Enable/start `techbro-web.service` and `techbro-daily.timer`. Check
   `http://127.0.0.1:8000/health`, journal logs, and the timer schedule. External
   requests without credentials should receive `401`.
7. Run `systemctl start techbro-daily.service` for a live pipeline check. It scans
   once, uses the installed interpreter for all stages, stops on failure, and
   logs to `data/pipeline.log`. It runs at 09:00 Asia/Jakarta.

The web service binds to loopback and is read-only except for video output.
Its supplied service configuration enables local video rendering. Use one worker
so the process lock serializes renders. Keep swap on a small VPS, back up runtime
artifacts separately, and deploy tested revisions rather than modifying files
inside the installed package.

The optional manual renderer is `uv run --locked techbro render --help`. It
requires reviewed local clips, a JSON video plan, and a narration file. It writes
MP4, subtitle, and credit sidecars. Review narration, footage rights, and subtitle
alignment before publishing.
