"""Isolated fixtures and network guards for deterministic tests."""

import os
import urllib.request

import httpx
import pytest

from techbro_pipeline import build_dataset, build_threads_draft, scan, sources, topic_tracker
from techbro_pipeline.web import main


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    data = tmp_path / "data"
    dataset = tmp_path / "dataset"
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setenv("DATASET_DIR", str(dataset))
    monkeypatch.setenv("CREDS_FILE", str(tmp_path / "missing-creds.json"))
    monkeypatch.delenv("ADACODE_API_KEY", raising=False)
    monkeypatch.delenv("ENABLE_SUPPLEMENTAL_RSS", raising=False)
    for key in list(os.environ):
        if key.startswith(("REPLIZ_", "THREADS_")):
            monkeypatch.delenv(key)
    for module in (scan, sources, topic_tracker, build_threads_draft, build_dataset):
        monkeypatch.setattr(module, "DATA", str(data))
    monkeypatch.setattr(build_dataset, "OUT", str(dataset))
    monkeypatch.setattr(scan, "CREDS", str(tmp_path / "missing-creds.json"))
    monkeypatch.setattr(topic_tracker, "KEY", "")
    monkeypatch.setattr(main, "DATA_DIR", str(data))
    monkeypatch.setattr(main, "ADACODE_KEY", "")
    monkeypatch.setattr(main, "VIDEO_RENDER_ENABLED", False)

    def forbid_network(*args, **kwargs):
        raise AssertionError("A deterministic test attempted external network access")

    monkeypatch.setattr(urllib.request, "urlopen", forbid_network)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", forbid_network)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbid_network)
    return data, dataset


@pytest.fixture
def sample_topic():
    return {
        "topic": "Observability",
        "count": 2,
        "summary": "Contoh software dapat diamati. Ini membantu menemukan kegagalan.",
        "context": "Observability menjelaskan keadaan sistem.",
        "value_added": "Analisis: data pengamatan membantu perbaikan.",
        "handles": ["fictional_builder"],
        "days": ["2026-01-01"],
    }
