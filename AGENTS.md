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

## Everyday Techbro publishing

Use the repository's `./techbro` launcher for local operations. It selects the
project directory, installed environment and local `.env`. A local `techbro`
command may point to this launcher, so agents can use the same shortcuts:

- `techbro antrean`: list jobs; no approval or dispatch.
- `techbro lihat`: show today's source draft; `techbro lihat YYYYMMDD` selects a date.
- `techbro lihat JOB_ID`: show the exact saved queued release for review.
- `techbro siapkan`: run collection through dataset, then enqueue when configured.
- `techbro setujui JOB_ID`: approve that reviewed job; no dispatch.
- `techbro kirim`: process already approved, due jobs in the workspace.

Requests to prepare or display a draft do not authorize publication. When the
user authorizes publishing a specific reviewed release, use that job ID for
approval and then dispatch; retain authorization already given in the session.
Never approve an unspecified job merely to make the worker do something.
Native Threads polling can require another worker invocation after a delay.
Inspect `workflow status` and `workflow events` on failure or uncertainty.
Preserve legacy receipts; enqueue rejects dates with recorded legacy submissions.
See `docs/ai-workflow.md` for setup and detailed operations. Implementation still
belongs in the package; the launcher is only a compatibility entrypoint.
