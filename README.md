# Techbro Pipeline

Collect a technology timeline and news feeds, build editorial topic summaries
and reviewable Threads drafts, export CSV datasets, and browse them in a FastAPI
dashboard. The optional Node tool produces Markdown summaries from X.

## Quick start (no credentials required)

Prerequisites: Git, Python 3.11–3.14, and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Linux is required for the scheduled pipeline lock and native deployment.
Linux is the supported and tested platform for the complete application.

```sh
git clone https://github.com/israhabibi/techbro-pipeline.git
cd techbro-pipeline
uv sync --locked
uv run --locked techbro demo
uv run --locked techbro serve
```

Open `http://127.0.0.1:8000`. The demo uses fictional accounts and locally generated
topics; it never calls X, a model provider, or news services. It writes under
`data/` and `dataset/`. Run it in a fresh checkout or set `DATA_DIR` and
`DATASET_DIR` to separate demo directories before running it.

## Commands

On an already configured checkout, `./techbro` selects the local environment and
configuration automatically. These shortcuts cover daily draft review and posting:

```sh
./techbro antrean          # list jobs
./techbro lihat            # show today's draft
./techbro lihat JOB_ID     # review the exact queued release
./techbro siapkan          # collect and prepare a new draft
./techbro setujui JOB_ID   # approve the reviewed job
./techbro kirim            # process already approved jobs
```

The [ai-workflow guide](docs/ai-workflow.md) explains installing a `techbro`
shortcut that works from any directory and the separation of review and dispatch.

```sh
make test       # Python tests; no credentials or external services
make lint       # Static checks and formatting verification
make check      # Lint, tests, optional Node tests, and package build
make demo       # Offline pipeline and synthetic data
make dev        # Dashboard on localhost:8000
make build      # Wheel and source distribution
make audit      # Dependency vulnerability audit (network required)
```

Install Node 22+ to test or run the optional JavaScript summarizer:

```sh
npm test
npm run summarize -- --help
```

Python tests can be focused with `uv run --locked pytest tests/test_pipeline.py`.
Coverage: `uv run --locked pytest --cov --cov-report=term-missing`.
Optional analysis dependencies are locked too:
`uv run --locked --extra analysis python dataset/sample_code.py` analyzes the
generated exports. The exploratory notebook uses the same extra; run it from
`dataset/` after generating demo or live exports.

## Live integrations

Copy `.env.example` to `.env` and replace placeholders. Python loads configuration
from the environment; Compose reads `.env` automatically. For a local shell,
export the required variables explicitly or run with `uv run --env-file .env`.
The installed CLI also accepts `techbro --env-file .env pipeline`. The legacy
`pipeline_daily.sh` launcher loads its local `.env` explicitly and enables RSS
unless `ENABLE_SUPPLEMENTAL_RSS` is already set to another value.
X credentials are supplied via `CREDS_FILE`; the scanner needs JSON string fields
`bearer`, `auth_token`, and `ct0`, with optional `twid` and `kdt`. Use
`creds.example.json` as the shape, never as working credentials.

```sh
uv run --locked --env-file .env techbro pipeline
```

The ordered stages are scan → RSS sources → topics → Threads draft → CSV dataset.
They run in the same interpreter and stop on failure. Failed collection or topic
extraction preserves previous artifacts. RSS is optional unless explicitly enabled
with `ENABLE_SUPPLEMENTAL_RSS=1`. Publishing is off by default. The optional
[official Meta Threads integration](docs/meta-threads.md) previews drafts and
publishes ordered reply chains. Set `THREADS_AUTO_PUBLISH=true` only to opt into
immediate publishing after all pipeline stages succeed. For scheduled posting,
run the pipeline through cron/systemd at the desired time. The alternative
[Repliz integration](docs/repliz.md) remains optional; enabling both publishers is
rejected before a pipeline run.
The [shared ai-workflow integration](docs/ai-workflow.md) can enqueue daily drafts
after successful stages and provides `techbro workflow` commands for preview,
explicit approval, worker dispatch, and status. Enable it with
`AI_WORKFLOW_AUTO_ENQUEUE=true` and disable both legacy automatic publishers.
Existing legacy publishing receipts prevent re-enqueueing that date.
The X session interface is unofficial and can change; valid credentials do not
guarantee access. Live model extraction and chat require `ADACODE_API_KEY`.

Configuration:

| Variable | Default / purpose |
| --- | --- |
| `DATA_DIR` | `./data`; shared pipeline and dashboard artifacts |
| `DATASET_DIR` | `dataset` beside `DATA_DIR`; generated CSV exports |
| `CREDS_FILE` | `./creds.json`; X session credentials |
| `SCAN_PAGES` | `3`; number of X timeline pages, 1–100 |
| `ADACODE_API_KEY` | Unset; live topics and chat |
| `ADACODE_MODEL` | `adacode-2.0` |
| `ENABLE_SUPPLEMENTAL_RSS` | Off; set to `1` to fetch news |
| `ENABLE_VIDEO_RENDER` | Off; set to `true` to enable rendering |
| `TTS_BACKEND` | `local`; `edge` opts into the online TTS extra |
| `PEXELS_API_KEY` | Unset; optional preferred video provider |
| `VIDEO_ASSETS_DIR` | Unset; optional administrator-selected scene directory |
| `THREADS_APP_ID` | Unset; Threads app identity for Meta setup; posting uses the user token |
| `THREADS_ACCESS_TOKEN` | Unset; Threads user access token with publishing permission |
| `THREADS_USER_ID` | Unset; explicit target from `techbro meta profile`, distinct from app ID |
| `THREADS_MEDIA_PUBLIC_BASE_URL` | Unset; public HTTPS origin Meta uses to fetch rendered video files |
| `THREADS_AUTO_PUBLISH` | `false`; opt into immediate Meta publishing after a successful pipeline |
| `REPLIZ_ACCESS_KEY` / `REPLIZ_SECRET_KEY` | Unset; server-side Repliz API credentials |
| `REPLIZ_ACCOUNT_ID` | Unset; connected Threads account ID |
| `REPLIZ_AUTO_SCHEDULE` | `false`; opt into live scheduling after a successful pipeline |
| `REPLIZ_SCHEDULE_TIME` | Unset; required daily publish time, HH:MM in Asia/Jakarta |
| `AI_WORKFLOW_EXECUTABLE` | `ai-workflow`; separately installed executable, or its absolute path |
| `AI_WORKFLOW_HOME` | `DATA_DIR/workflow`; private reviewed outbox |
| `AI_WORKFLOW_ACCOUNT` | `techbro-threads`; explicit target account name |
| `AI_WORKFLOW_AUTO_ENQUEUE` | `false`; queue a draft after successful stages; approval remains explicit |
| `TIME_ZONE` | JavaScript summarizer only; default `Asia/Jakarta` |

Pipeline artifacts consistently use the Asia/Jakarta calendar date. The raw
tweet timestamps remain unchanged; exported tweet dates use that local zone.

The daily video studio can fetch clips from Wikimedia Commons without an API
key when Pexels is unavailable. It automatically accepts only CC0, public
domain, or CC BY clips, records creator/source/license details in the credits
file, and falls back to locally generated motion cards when no compatible clip
is available. Review the credits and comply with each file's license before
publishing the rendered video.

## Deployment

```sh
docker compose build digest
docker compose up -d --no-deps digest
curl --fail http://127.0.0.1:8000/health
```

The default Compose service exposes the dashboard only on localhost, runs as a
non-root user, and mounts `data/` and `dataset/`. A new checkout starts with an
empty dashboard until a demo or live pipeline has run. Enable video generation
explicitly; the image includes FFmpeg, eSpeak NG, and DejaVu fonts. Existing data
must be writable by container UID 1000 for generated videos.

The video studio can publish a rendered MP4 to Threads after an explicit button
click. Configure the Threads token and user ID plus
`THREADS_MEDIA_PUBLIC_BASE_URL`; Meta must be able to fetch the video from that
HTTPS origin. The default local-only deployment cannot publish video until it
is reachable through a public HTTPS host. Text-only publishing does not need
this media URL.

Keep any existing reverse proxy separate. Optional ingress configuration is in
`deploy/ingress/`; authenticate the dashboard before exposing a personal timeline.
[Native deployment](deploy/native/README.md) covers systemd and Caddy.

On a Linux workstation, a cron entry can run the installed pipeline; use absolute
paths and define `DATA_DIR`, `DATASET_DIR`, and credentials in a protected environment:

```cron
0 9 * * * cd /path/to/techbro-pipeline && .venv/bin/techbro pipeline
```

The runner saves stage logs to `DATA_DIR/pipeline.log` and prevents overlapping
runs. Back up data and secrets separately from source code.

## Repository layout and contribution

See [architecture](docs/architecture.md), [contributing](CONTRIBUTING.md),
[security](SECURITY.md), and the [implementation plan](docs/implementation-plan.md).
Compatibility scripts at the root delegate to the package; implementation belongs
in `src/techbro_pipeline/`. Runtime data and exports are ignored by Git.

Repository visibility is unchanged. A source-code license must be selected by
the owner before distributing this as a licensed open-source release; third-party
timeline content and footage require their own rights review.
