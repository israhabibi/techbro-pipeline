.PHONY: test lint format check demo dev build audit

test:
	uv run --locked pytest

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

check: lint test
	npm run lint
	npm test
	uv build

demo:
	uv run --locked techbro demo

dev:
	uv run --locked techbro serve

build:
	uv build

audit:
	uv export --locked --no-dev --no-emit-project --output-file /tmp/techbro-audit-requirements.txt >/dev/null
	uv run --locked pip-audit --require-hashes --disable-pip --no-deps -r /tmp/techbro-audit-requirements.txt
