# Setup

The supported, verified setup is in [README.md](README.md).

- Install: `uv sync --locked`, and `npm ci` for JavaScript checks.
- Offline verification: `make check` and `uv run --locked python scripts/smoke.py`.
- Synthetic demo: `make demo`, then `make dev`.
- Live run: create ignored `.env` and `creds.json` from sanitized examples, then
  `.venv/bin/techbro --env-file .env pipeline`.
- Local containers: `docker compose build digest` and
  `docker compose up -d --no-deps digest`.
- Clean remote checkout: `uv run --locked python scripts/verify_checkout.py`.
- Native systemd: [deploy/native/README.md](deploy/native/README.md).

Do not install unpinned dependencies or copy an existing virtual environment.
The Git checkout contains code and synthetic examples, not live data or credentials.
