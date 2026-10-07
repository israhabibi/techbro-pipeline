# Release-readiness and reproducibility plan

Goal: make this repository installable, testable, and runnable from a fresh Git
checkout; deploy locally and verify the pushed revision independently.
Repository visibility stays unchanged. Production data and secrets remain local.

## Architecture

- `src/techbro_pipeline/`: installable Python package, grouped by pipeline stage.
- `src/techbro_pipeline/web/`: FastAPI API, templates, status, and video generation.
- `src/x-summary.mjs`: optional standalone Node summarizer.
- `tests/`: deterministic Python and JavaScript tests using synthetic data.
- `scripts/`: documented quality and clean-checkout verification commands.
- `deploy/`: portable local container and optional native service configuration.
- Configuration: environment variables and explicit paths; no ancestor-directory
  credentials, import-time writes, or dependence on an existing working directory.
- Artifact writes: atomic JSON replacement; failed jobs preserve previous output.
- External boundaries: HTTP clients and media executables are mocked in unit
  tests; offline demo mode exercises the complete pipeline from synthetic inputs.

## Execution and acceptance checks

1. Establish a passing baseline and fix stage exit codes, duplicate scans,
   configuration paths, time zones, status reporting, and API validation.
2. Introduce a package manifest, dependency lock, formatter, linter, and CI.
3. Test classification, collection windows, draft limits, CSV generation,
   pipeline failures, dashboard endpoints, chat validation, and video handling.
4. Document prerequisites, offline demo, live integrations, contributing,
   architecture, security reporting, and local/native deployment.
5. Build and smoke-test a non-root container without credentials. Preserve live
   data when replacing the existing local dashboard container.
6. Commit and push changes, deploy the tested revision locally, clone from the
   remote into a new directory, install locked dependencies, run all quality
   checks and the demo, start the server, and verify its HTTP endpoints.
7. Fix and repeat any failed check. Record actual commands, results, commit ID,
   and remaining external prerequisites. Do not equate mock tests with live
   service validation or change repository visibility.

## Baseline

- Node: six tests passing.
- Python: no automated tests or CI; incomplete dependencies and no package.
- Existing deployment: Docker container `digest-web`, host port 8000, data bind
  mount from this checkout. Keep the existing shared reverse proxy running.
- Known defects: ignored topic-extraction exit status, scanner failure written
  as empty success, duplicate native scans, inconsistent UTC/Jakarta dates,
  ignored `DATA_DIR`, pending status reported as OK, incomplete container mounts.

## Progress

- [x] Inspect baseline and establish authorized local deployment scope.
- [x] Implement package, configuration, correctness, and validation changes.
- [x] Add and pass tests, static checks, dependency checks, and packaging checks.
- [x] Verify clean installation and container runtime without local inputs.
- [ ] Commit, push, deploy locally, and verify a fresh remote clone.
