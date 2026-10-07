import httpx
import pytest
from fastapi.testclient import TestClient

from techbro_pipeline import demo
from techbro_pipeline.config import day_stamp
from techbro_pipeline.web import main
from techbro_pipeline.web.video_generation import VideoGenerationError


@pytest.fixture
def client():
    with TestClient(main.app) as value:
        yield value


@pytest.mark.parametrize("url", ["/", "/daily", "/status", "/topics-timeline", "/health"])
def test_empty_dashboard_starts_without_secrets(client, url):
    assert client.get(url).status_code == 200


def test_health_exposes_no_configuration(client):
    assert client.get("/health").json() == {"ok": True}


def test_dashboard_tolerates_corrupt_or_wrong_shape_artifacts(client, isolated_runtime):
    data, _ = isolated_runtime
    (data / "feed").mkdir(parents=True)
    (data / "feed" / "feed_20260101.json").write_text("[]", encoding="utf-8")
    (data / "topics").mkdir()
    (data / "topics" / "topics_20260101.json").write_text("bad-json", encoding="utf-8")
    assert client.get("/daily").status_code == 200
    assert client.get("/api/daily/20260101/tweets").json()["total"] == 0


def test_demo_dashboard_renders_and_paginates(client):
    demo.main()
    day = day_stamp()
    for route in ("/", "/daily", "/status", "/topics-timeline"):
        response = client.get(route)
        assert response.status_code == 200
        assert (
            "Observability" in response.text if route != "/status" else "Pipeline" in response.text
        )
    response = client.get(f"/api/daily/{day}/tweets?limit=1&techbro_only=true")
    assert response.json()["total"] == 1
    assert response.json()["tweets"][0]["user"] == "fictional_builder"
    assert client.get(f"/api/daily/{day}/tweets?limit=0").status_code == 422
    assert client.get("/api/daily/20000101/tweets").status_code == 404
    assert client.get("/api/status").json()["overall"] == "ok"


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"message": 3},
        {"message": " "},
        {"message": "x" * 4001},
        {"message": "hello", "history": [{}]},
        {"message": "hello", "history": [{"role": "system", "content": "bad"}]},
        {"message": "hello", "history": [{"role": "user", "content": "x"}] * 13},
    ],
)
def test_invalid_chat_returns_validation_error(client, payload, monkeypatch):
    monkeypatch.setattr(main, "ADACODE_KEY", "fake-test-key")
    assert client.post("/api/chat", json=payload).status_code == 422


def test_chat_without_key_reports_unavailable(client):
    assert client.post("/api/chat", json={"message": "hello"}).status_code == 503


def test_chat_uses_validated_history_and_returns_provider_reply(client, monkeypatch):
    monkeypatch.setattr(main, "ADACODE_KEY", "fake-test-key")
    received = []

    async def provider(self, url, **kwargs):
        received.extend(kwargs["json"]["messages"])
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "demo reply"}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", provider)
    response = client.post(
        "/api/chat", json={"message": " hello ", "history": [{"role": "user", "content": "prior"}]}
    )
    assert response.json() == {"reply": "demo reply"}
    assert received[-1] == {"role": "user", "content": "hello"}
    assert received[-2]["content"] == "prior"


def test_provider_errors_are_sanitized(client, monkeypatch):
    monkeypatch.setattr(main, "ADACODE_KEY", "fake-test-key")

    async def provider(self, url, **kwargs):
        raise httpx.ConnectError("private diagnostic contains fake secret")

    monkeypatch.setattr(httpx.AsyncClient, "post", provider)
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 502
    assert "private" not in response.text


def test_video_requires_enabled_feature_and_rejects_client_filesystem_path(client, monkeypatch):
    day = day_stamp()
    demo.main()
    assert client.post(f"/api/daily/{day}/video", json={"voiceover": "Demo."}).status_code == 503
    monkeypatch.setattr(main, "VIDEO_RENDER_ENABLED", True)
    assert (
        client.post(
            f"/api/daily/{day}/video", json={"voiceover": "Demo.", "assets_dir": "/etc"}
        ).status_code
        == 422
    )
    assert client.post(f"/api/daily/{day}/video", json={"voiceover": "x" * 1801}).status_code == 422
    assert client.post(f"/api/daily/{day}/video", content="bad-json").status_code == 400


def test_failed_video_releases_render_lock(client, monkeypatch):
    demo.main()
    monkeypatch.setattr(main, "VIDEO_RENDER_ENABLED", True)

    def render(*args):
        raise VideoGenerationError("synthetic render failure")

    monkeypatch.setattr(main, "render_daily_video", render)
    for _ in range(2):
        assert (
            client.post(f"/api/daily/{day_stamp()}/video", json={"voiceover": "Demo."}).status_code
            == 503
        )
    assert not main.VIDEO_RENDER_LOCK.locked()


def test_successful_video_response_and_safe_download(client, isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    demo.main()
    monkeypatch.setattr(main, "VIDEO_RENDER_ENABLED", True)
    day = day_stamp()
    filename = f"techbro-{day}-120000-abcd1234.mp4"
    folder = data / "videos" / day
    folder.mkdir(parents=True)
    (folder / filename).write_bytes(b"synthetic fixture video")
    monkeypatch.setattr(
        main,
        "render_daily_video",
        lambda *args: {
            "filename": filename,
            "srt": filename.replace(".mp4", ".srt"),
            "credits": filename.replace(".mp4", ".credits.txt"),
        },
    )
    response = client.post(f"/api/daily/{day}/video", json={"voiceover": "Demo."})
    assert response.status_code == 200
    assert client.get(response.json()["video_url"]).content == b"synthetic fixture video"
    assert client.get(f"/api/daily/{day}/video/secrets.json").status_code == 404
    assert len(client.get(f"/api/daily/{day}/videos").json()["videos"]) == 1
