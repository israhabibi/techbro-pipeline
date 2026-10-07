import csv
import json

import pytest

from techbro_pipeline import build_dataset, build_threads_draft
from techbro_pipeline.config import Settings, write_csv, write_json


def test_settings_use_explicit_paths_not_parent_credentials(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CREDS_FILE")
    assert Settings.from_env().credentials_file == tmp_path / "creds.json"


def test_json_write_failure_preserves_previous_content(tmp_path):
    destination = tmp_path / "demo.json"
    write_json(destination, {"old": True})
    try:
        write_json(destination, {"unserializable": object()})
    except TypeError:
        pass
    assert json.loads(destination.read_text()) == {"old": True}
    assert list(tmp_path.iterdir()) == [destination]


def test_csv_write_failure_preserves_previous_export(tmp_path):
    path = tmp_path / "demo.csv"
    write_csv(path, ["id"], [{"id": "previous"}])
    before = path.read_bytes()
    with pytest.raises(ValueError):
        write_csv(path, ["id"], [{"id": "new", "unexpected": "field"}])
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_artifact_permissions_allow_the_shared_service_group(tmp_path):
    import stat

    path = tmp_path / "shared.json"
    write_json(path, {"demo": True})
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    path = tmp_path / "shared.csv"
    write_csv(path, ["id"], [{"id": "demo"}])
    assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_drafts_have_sequential_numbering_and_fit_post_limit(sample_topic):
    topic = dict(
        sample_topic,
        topic="t" * 700,
        summary=("Long complete sentence. " * 100),
        handles=["demo" * 300],
    )
    parts = build_threads_draft.make_parts({"topics": [topic], "total_tweets_scanned": 2})
    assert [part["number"] for part in parts] == [1, 2, 3]
    assert all(len(part["text"]) <= 500 for part in parts)
    assert parts[1]["text"].startswith("2/3 — ")


def test_no_topics_produces_no_draft():
    assert build_threads_draft.make_parts({"topics": []}) == []


def test_dataset_deduplicates_and_filters_month(isolated_runtime):
    data, dataset = isolated_runtime
    tweet = {
        "id": "demo",
        "user": "@fictional",
        "text": "Python\nexample",
        "created_at": "Wed Dec 31 18:00:00 +0000 2025",
        "is_techbro_id": True,
        "user_score": 3,
        "user_reasons": ["tweet:python"],
    }
    for day in ("20260101", "20260102"):
        write_json(data / "feed" / f"feed_{day}.json", {"tweets": [tweet]})
    rows = build_dataset.build_tweets("2026-01")
    assert len(rows) == 1
    assert rows[0]["day"] == "2026-01-01"
    assert rows[0]["text"] == "Python example"
    assert build_dataset.build_tweets("2025-12") == []
    activity = build_dataset.build_activity("2026-01")
    assert activity[0]["tweet_count"] == 1
    with (dataset / "techbro_tweets.csv").open() as handle:
        assert len(list(csv.DictReader(handle))) == 1


def test_empty_topics_export_creates_header_and_removes_stale_rows(isolated_runtime):
    _, dataset = isolated_runtime
    dataset.mkdir()
    (dataset / "techbro_topics.csv").write_text("stale-data", encoding="utf-8")
    assert build_dataset.build_topics() == []
    assert (dataset / "techbro_topics.csv").read_text().startswith("topic,tweet_count,")
