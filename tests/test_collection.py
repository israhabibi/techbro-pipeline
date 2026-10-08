import datetime
import io
import json
import urllib.error

import pytest

from techbro_pipeline import scan, sources, topic_tracker
from techbro_pipeline.config import day_stamp, write_json


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Belajar Kubernetes", "kubernetes"),
        ("ngoding Python", "python"),
        ("Cuaca cerah hari ini", None),
        ("A happy capital city", None),
        (None, None),
        ("API baru untuk software", "software"),
    ],
)
def test_recognizes_technical_terms_without_substring_matches(text, expected):
    assert scan.detect_tech_tweet(text) == expected


def test_classifies_indonesian_engineer_and_excludes_unrelated_profile():
    assert scan.classify_user({"location": "Jakarta", "description": "Software engineer"})[0]
    assert not scan.classify_user({"location": "London", "description": "Traveler"})[0]
    assert not scan.classify_user({"location": "Jakarta", "description": "Hair stylist"})[0]
    assert scan.classify_user({"location": "Jakarta", "description": "AI tools builder"})[0]


def test_scanner_failure_preserves_previous_feed(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    previous = data / "feed" / f"feed_{day_stamp()}.json"
    write_json(previous, {"tweets": [{"id": "old-demo"}]})
    monkeypatch.setattr(scan, "load_creds", lambda: {})

    def failure(*args, **kwargs):
        raise urllib.error.URLError("synthetic outage")

    monkeypatch.setattr(scan, "fetch_timeline", failure)
    assert scan.main(1) == 1
    assert json.loads(previous.read_text())["tweets"] == [{"id": "old-demo"}]


def test_scanner_rejects_unsupported_response(monkeypatch):
    monkeypatch.setattr(scan, "load_creds", lambda: {})
    monkeypatch.setattr(scan, "fetch_timeline", lambda *args, **kwargs: {"errors": []})
    assert scan.main(1) == 1


def test_technical_tweet_does_not_make_global_account_indonesian(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    monkeypatch.setattr(scan, "load_creds", lambda: {})
    monkeypatch.setattr(
        scan,
        "fetch_timeline",
        lambda *args, **kwargs: {
            "globalObjects": {
                "tweets": {
                    "demo-1": {
                        "text": "Belajar Kubernetes",
                        "user_id_str": "u1",
                        "created_at": "Thu Jan 01 01:00:00 +0000 2026",
                    }
                },
                "users": {"u1": {"screen_name": "fictional_builder"}},
            },
        },
    )
    assert scan.main(1) is None
    feed = json.loads((data / "feed" / f"feed_{day_stamp()}.json").read_text())
    assert feed["tweets"][0]["is_techbro_id"] is False
    assert feed["tweets"][0]["is_tech_tweet"] is True
    assert feed["tweets"][0]["tweet_tech_signal"] == "kubernetes"
    assert feed["users"][0]["reasons"] == ["tweet:kubernetes"]


def test_partial_scan_failure_does_not_replace_feed(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    monkeypatch.setattr(scan, "load_creds", lambda: {})
    count = 0

    def timeline(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise TimeoutError("synthetic timeout")
        return {
            "globalObjects": {"tweets": {}, "users": {}},
            "timeline": {
                "instructions": [
                    {
                        "entries": [
                            {
                                "content": {
                                    "operation": {
                                        "cursor": {
                                            "cursorType": "Bottom",
                                            "value": "next",
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ],
            },
        }

    monkeypatch.setattr(scan, "fetch_timeline", timeline)
    monkeypatch.setattr(scan.time, "sleep", lambda _: None)
    assert scan.main(2) == 1
    assert not list(data.glob("feed/*.json"))


def test_credentials_missing_or_invalid_fail_without_network(tmp_path, monkeypatch):
    with pytest.raises(FileNotFoundError):
        scan.load_creds()
    path = tmp_path / "fake-creds.json"
    path.write_text('{"auth_token": 1}', encoding="utf-8")
    monkeypatch.setattr(scan, "CREDS", str(path))
    with pytest.raises(ValueError, match="nonempty"):
        scan.load_creds()


def test_collect_tweets_applies_time_window_and_deduplicates(isolated_runtime):
    data, _ = isolated_runtime
    now = datetime.datetime.now(datetime.UTC)

    def tweet(identifier, timestamp, **extra):
        return {
            "id": identifier,
            "is_techbro_id": True,
            "is_tech_tweet": True,
            "user": "fictional_builder",
            "text": "Python example",
            "created_at": timestamp.strftime("%a %b %d %H:%M:%S %z %Y"),
            **extra,
        }

    items = [
        tweet("recent", now - datetime.timedelta(hours=1)),
        tweet("expired", now - datetime.timedelta(hours=25)),
        tweet("future", now + datetime.timedelta(hours=1)),
        tweet("general", now, is_tech_tweet=False),
    ]
    write_json(data / "feed" / "feed_20260101.json", {"tweets": items})
    write_json(data / "feed" / "feed_20260102.json", {"tweets": items})
    result = topic_tracker.collect_tweets()
    assert [item["user"] for item in result] == ["fictional_builder"]
    assert "WIB" in result[0]["day"]


def test_topic_failure_returns_nonzero_and_preserves_previous_output(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    previous = data / "topics" / f"topics_{day_stamp()}.json"
    write_json(previous, {"topics": [{"topic": "previous"}]})
    monkeypatch.setattr(topic_tracker, "collect_tweets", lambda: [{"text": "sample"}])
    monkeypatch.setattr(topic_tracker, "extract_topics", lambda _: [])
    assert topic_tracker.main() == 1
    assert json.loads(previous.read_text())["topics"][0]["topic"] == "previous"


@pytest.mark.parametrize(
    "content",
    [
        '{"topic":"wrong-shape"}',
        '["bad"]',
        '[{"topic":"missing-count","summary":"example"}]',
        "not json",
    ],
)
def test_invalid_model_response_is_rejected(content, monkeypatch):
    monkeypatch.setattr(topic_tracker, "KEY", "fake-test-key")
    payload = {"choices": [{"message": {"content": content}}]}
    monkeypatch.setattr(
        topic_tracker.urllib.request,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()),
    )
    assert (
        topic_tracker.extract_topics([{"day": "demo", "user": "fictional", "text": "Python"}]) == []
    )


def test_valid_model_response_is_accepted(sample_topic, monkeypatch):
    monkeypatch.setattr(topic_tracker, "KEY", "fake-test-key")
    payload = {"choices": [{"message": {"content": json.dumps([sample_topic])}}]}
    monkeypatch.setattr(
        topic_tracker.urllib.request,
        "urlopen",
        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()),
    )
    assert topic_tracker.extract_topics(
        [{"day": "demo", "user": "fictional", "text": "Python"}]
    ) == [sample_topic]


def test_rss_parser_extracts_items_without_network(monkeypatch):
    rss = b"<rss><channel><item><title>Demo title</title><link>https://example.test</link></item></channel></rss>"
    monkeypatch.setattr(sources.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(rss))
    result = sources.fetch_google_news("software")
    assert result[0]["title"] == "Demo title"


def test_rss_total_failure_preserves_artifact(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    monkeypatch.setenv("ENABLE_SUPPLEMENTAL_RSS", "1")
    monkeypatch.setattr(sources, "fetch_google_news", lambda _: [])
    monkeypatch.setattr(sources, "fetch_tempo_rss", lambda: [])
    assert sources.main() == 1
    assert not list(data.glob("sources/*.json"))
