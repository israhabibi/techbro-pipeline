# Verification record

Verified on 7 October 2026 (Asia/Jakarta). This record distinguishes deterministic
and offline runtime checks from live account-dependent integrations.

## Pre-deployment results

- 70 Python tests pass; Python 3.11 and 3.14 are verified.
- 10 Node tests passed; Ruff, ESLint, and formatting checks passed.
- Python runtime dependency audit and npm dependency audit reported no known
  vulnerabilities at the time of verification.
- Wheel and source distribution built. Artifact names were checked for excluded
  credential files and runtime data; the wheel contains dashboard templates.
- A separate virtual environment installed the wheel and locked runtime
  requirements. The demo and real HTTP server passed checks from outside the
  checkout: health, archive, status, topics, and pagination.
- A non-root container with networking disabled ran the synthetic demo and
  generated a real MP4, subtitles, and credits. FFprobe confirmed audio and video
  streams; the sample narration lasted approximately three seconds.
- Native deployment was documented and corrected, but not deployed; this task's
  authorized deployment target is the existing local Docker dashboard.

## Repeatable checks

The local `digest-web` container was replaced successfully after a separate
container passed HTTP checks without credentials. Existing data/dataset mounts
were preserved, the dashboard now binds to localhost, and the existing shared
Traefik container was left running. `/health`, `/daily`, `/status`,
`/topics-timeline`, and `/api/status` returned successful responses after deployment.

The first independent remote checkout at `7a4885e` passed clean installation,
all quality checks, audits, and HTTP startup. A transient Docker startup
connection reset prompted a verifier retry fix and an additional regression
test before the final post-deployment pull and verification.

```sh
uv sync --locked
npm ci
make check
uv run --locked python scripts/smoke.py
make audit
npm audit --audit-level=high
uv run --locked python scripts/verify_checkout.py
```

The final command independently clones the pushed revision, creates a fresh
environment, runs quality/build/audit checks, and starts a real server with its
own synthetic data. Failed checkouts are retained for diagnosis. A successful
run must leave tracked source unchanged.

## External prerequisites and release scope

Live X session scraping, model generation, Pexels footage, and online TTS require
external access and credentials; deterministic tests mock these boundaries.
Offline verification proves local code/install/runtime behavior and local media
rendering, not that a live account remains authorized or an upstream API will
remain compatible. No live-account calls are required for a fresh-checkout demo.

Repository visibility remains unchanged. The owner has not selected a source
license yet. Previously tracked timeline CSVs and personal ingress files have
been removed from the current source tree while preserved locally. Older Git
history still contains historical dataset commits; do not interpret this change
as a history purge or as approval to publish that history.
