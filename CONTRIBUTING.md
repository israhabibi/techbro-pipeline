# Contributing

Create a branch from `main`, install with `uv sync --locked` and `npm ci`, and
run `make check`. Use `make format` and `npm run format` before submitting changes.
Test observable behavior using fictional data; never connect unit tests to a
real account or external provider. Submit a focused pull request explaining the
problem, resulting behavior, tests run, and any migration or configuration steps.

Dependencies are declared in `pyproject.toml` and `package.json`, and locked in
`uv.lock` and `package-lock.json`. Commit manifest and lock changes together.
Use `uv lock --upgrade-package NAME` for targeted Python updates, followed by
tests and `make audit`. Use `npm audit` for JavaScript tooling dependencies.

Pipeline stages are callable independently and run in order through `techbro
pipeline`. Do not add publishing to the default pipeline: drafts require review.
Keep the optional live integration prerequisites separate from offline verification.

Before merging release changes, build the container, smoke-test it, and run
`uv run --locked python scripts/verify_checkout.py` against the pushed revision.
The verifier creates its own virtual environment, synthetic data, and temporary
server. It never copies `.env`, credentials, or runtime artifacts.
