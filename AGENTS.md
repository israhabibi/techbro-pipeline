# Repository guidelines

Implementation belongs in `src/techbro_pipeline/`, grouped by pipeline stage,
or `src/x-summary.mjs`. Python dashboard templates are package resources under
`src/techbro_pipeline/web/templates/`. Root Python files are compatibility
launchers, not a second implementation.

Use Python 3.11–3.14 and `uv sync --locked`. Commands: `make test`, `make lint`,
`make check`, `make demo`, `make dev`, `make build`, and `make audit`. Node 22+
and `npm ci` are required for the JavaScript checks. Format Python with Ruff
and JavaScript with Prettier; run Ruff and ESLint before committing.

Add observable-behavior tests for every behavior change or fix. Keep them
deterministic; network calls, subprocesses, and credentials belong behind mocks
or synthetic fixtures. Run `uv run --locked pytest tests/test_web.py` for a
focused test and `uv run --locked pytest --cov` for coverage. The offline demo
and clean-checkout verifier must work without credentials or production data.

Use `Settings.from_env()` for artifact and credential paths. Do not read secrets
from parent folders or write files during imports. Failures must return nonzero
and preserve the previous usable artifact. Use atomic JSON writes.

Do not commit live credentials, cookies, `.env`, production datasets, runtime
logs, or personal host configuration. Use ignored local files, environment
variables, and sanitized examples. Never print secret values. Secrets and
production artifacts must not enter Docker's build context.

Use focused imperative commits. PRs explain the observable change, motivation,
verification, and configuration/migration steps; include screenshots for visual
changes. Before release, verify the remote Git revision in a new checkout using
`uv run --locked python scripts/verify_checkout.py`.
