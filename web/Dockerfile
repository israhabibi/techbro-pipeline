FROM ghcr.io/astral-sh/uv:0.11.13 AS uv
FROM python:3.11-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg espeak-ng fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock README.md ./
COPY src/techbro_pipeline ./src/techbro_pipeline
RUN uv sync --locked --no-dev --no-editable \
    && useradd --uid 1000 --create-home app \
    && mkdir /data /dataset && chown app:app /data /dataset
ENV PATH="/app/.venv/bin:$PATH" DATA_DIR=/data DATASET_DIR=/dataset PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "techbro_pipeline.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "24"]
