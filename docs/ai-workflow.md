# Shared reviewed publishing with ai-workflow

Techbro can send its daily Threads text drafts to `ai-workflow`, a separately
installed publishing CLI. The normal collection, topic, draft and dataset stages
remain Techbro's editorial pipeline. Successful runs can enqueue a draft;
approval and dispatch are separate explicit commands.

## Short commands for daily use

From this checkout, use `./techbro` instead of a long environment command. The
launcher automatically selects the project's installed Python environment and
loads its local `.env`. To use `techbro` from any directory, install a local link:

```sh
mkdir -p "$HOME/.local/bin"
ln -s "$(pwd)/techbro" "$HOME/.local/bin/techbro"
```

Make sure `$HOME/.local/bin` is on `PATH`. The link command deliberately refuses to
replace an existing command. The shortcuts are:

```sh
techbro antrean            # list queued jobs
techbro lihat              # show today's draft
techbro lihat JOB_ID       # show the exact saved job before approval
techbro siapkan            # run the pipeline and prepare a new draft
techbro setujui JOB_ID     # approve the reviewed job
techbro kirim              # process already approved jobs
```

`techbro lihat YYYYMMDD` selects a source draft date. `setujui` records the current
OS user as reviewer, or accepts `--reviewer NAME`. `kirim` never approves a draft;
it processes all already approved, due jobs in this private workspace. Container
polling can require running it again after a delay. Full commands remain available,
for example `techbro workflow status JOB_ID` and `techbro workflow events JOB_ID`.

Agents should display `lihat JOB_ID` before a publishing decision because the
source draft can change after enqueue. A request to prepare or show a draft does
not authorize approval or dispatch. Use publication authorization for the specific
reviewed release, including authorization already given earlier in the session.

## Configure once

Install `personal-ai-workflow` into a dedicated environment from its source:

```sh
uv venv /path/to/workflow-venv
uv pip install --python /path/to/workflow-venv/bin/python /path/to/ai-workflow
```

Add these settings to the ignored Techbro `.env`, preserving its existing account
configuration. Native publishing reuses `THREADS_USER_ID` and
`THREADS_ACCESS_TOKEN`; no token is copied into the workflow account document.

```dotenv
AI_WORKFLOW_EXECUTABLE=/path/to/workflow-venv/bin/ai-workflow
AI_WORKFLOW_ACCOUNT=techbro-threads
AI_WORKFLOW_AUTO_ENQUEUE=true
THREADS_AUTO_PUBLISH=false
REPLIZ_AUTO_SCHEDULE=false
```

`AI_WORKFLOW_HOME` defaults to `DATA_DIR/workflow`. Set it explicitly to share an
outbox across processes; keep that directory private and outside Git.
The executable setting is a single executable path, not a shell command.

```sh
uv run --locked techbro --env-file .env workflow setup --provider native
```

Setup creates a private workspace containing the explicit account ID and token
environment reference. It refuses to overwrite a different existing account.
The subprocess inherits the environment loaded from the explicitly selected
`.env` file. Installing or updating Techbro does not install ai-workflow.

For Repliz, use `--provider repliz` and configure `REPLIZ_ACCOUNT_ID`,
`REPLIZ_ACCESS_KEY` and `REPLIZ_SECRET_KEY`. A completed Repliz dispatch is
`scheduled`, not proof of final publication.

## Daily use

```sh
uv run --locked techbro --env-file .env pipeline
uv run --locked techbro --env-file .env workflow jobs
uv run --locked techbro --env-file .env workflow preview --date YYYYMMDD
```

The pipeline logs the new `job_id` after all five stages succeed. It never approves
or dispatches the job. The exact date's draft must exist and its recorded date must
match. Import preserves the first part and every ordered reply.

To enqueue an existing unpublished draft manually:

```sh
uv run --locked techbro --env-file .env workflow enqueue --date YYYYMMDD
```

The default release key is `daily-YYYYMMDD`. Re-enqueuing identical content returns
the existing job. Changed content requires a new key, supplied with `--key`, and
a new approval. `--at '2031-01-02T09:00:00+07:00'` schedules local dispatch.

Review the preview and account, then replace `JOB_ID` with the returned identifier:

```sh
uv run --locked techbro --env-file .env workflow approve JOB_ID --reviewer me
uv run --locked techbro --env-file .env workflow worker --steps 20
uv run --locked techbro --env-file .env workflow status JOB_ID
uv run --locked techbro --env-file .env workflow events JOB_ID
```

The worker processes approved, due jobs and can make live provider calls. Native
Threads containers and reply chains require polling delays; run the worker again
until the job completes, or schedule this bounded worker command periodically.
An uncertain remote write becomes `needs_review`; inspect the remote outcome
before retrying. `workflow cancel`, `recover`, and `retry` delegate to ai-workflow's
existing state checks. Native Threads uncertainty needs manual reconciliation
using the ai-workflow CLI and its operations guide.

## Migration and isolation

Switch off both legacy automatic publisher flags before setup, enqueue, approval
or worker dispatch. The pipeline rejects conflicting flags before collecting.
Stop any separately configured legacy publisher for the same release/account.
Independent publishing queues cannot deduplicate each other's writes.

Enqueue refuses any date with a legacy Meta or Repliz publishing receipt under
the same `DATA_DIR`, including uncertain receipts. Preview remains available.
Retain those receipts and begin with an unpublished release; do not delete
receipts to bypass this check. Drafts from before migration are not imported
automatically.

For an offline test, choose a separate `DATA_DIR` and `AI_WORKFLOW_HOME`, create
synthetic drafts with `techbro demo`, and run `workflow setup --provider mock`.
Use the same enqueue/approve/worker commands. A mock result has `demo=true` and
does not contact Threads. Unit tests inject subprocess results and prohibit
external provider requests; smoke checks remove workflow configuration.
