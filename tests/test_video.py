import json
import subprocess
from io import BytesIO
from urllib.parse import urlparse

import pytest

from techbro_pipeline import demo, render_video
from techbro_pipeline.config import day_stamp
from techbro_pipeline.web import video_generation as video


def test_subtitles_cover_narration_duration(tmp_path):
    path = tmp_path / "demo.srt"
    video._write_srt("Kalimat pertama. Kalimat kedua.", 5.0, path)
    text = path.read_text()
    assert "00:00:00,000" in text
    assert "00:00:05,000" in text
    assert "Kalimat pertama." in text


def test_video_validates_input_before_running_executables(tmp_path):
    with pytest.raises(video.VideoGenerationError, match="tanggal"):
        video.render_daily_video(tmp_path, "../../etc", "Demo.")
    with pytest.raises(video.VideoGenerationError, match="Naskah"):
        video.render_daily_video(tmp_path, "20260101", " ")


def test_missing_video_dependency_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setattr(video.shutil, "which", lambda _: None)
    with pytest.raises(video.VideoGenerationError, match="ffmpeg"):
        video.render_daily_video(tmp_path, "20260101", "Demo.")


@pytest.mark.parametrize(
    "license_name,expected",
    [("CC BY 4.0", True), ("CC BY-SA 4.0", False), ("CC BY-NC 4.0", False)],
)
def test_commons_video_search_checks_license_and_records_attribution(
    tmp_path, monkeypatch, license_name, expected
):
    class Response(BytesIO):
        headers = {"Content-Length": "4"}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

    def response(data):
        return Response(data if isinstance(data, bytes) else json.dumps(data).encode())

    def open_url(request, timeout):
        url = request.full_url
        if "generator=search" in url:
            return response(
                {
                    "query": {
                        "pages": {
                            "1": {
                                "title": "File:Demo.webm",
                                "imageinfo": [
                                    {
                                        "url": "https://upload.wikimedia.org/demo.webm",
                                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Demo.webm",
                                        "mime": "video/webm",
                                        "size": 4,
                                        "extmetadata": {
                                            "LicenseShortName": {"value": license_name},
                                            "LicenseUrl": {
                                                "value": "https://creativecommons.org/licenses/by/4.0/"
                                            },
                                            "Artist": {"value": "<a>Demo creator</a>"},
                                        },
                                    }
                                ],
                            }
                        }
                    }
                }
            )
        assert urlparse(url).hostname == "upload.wikimedia.org"
        return response(b"webm")

    monkeypatch.setattr(video.urllib.request, "urlopen", open_url)
    result = video._commons_asset("technology", tmp_path / "clip.mp4")
    if expected:
        asset, path = result
        assert path.suffix == ".webm"
        assert path.read_bytes() == b"webm"
        assert asset["creator"] == "Demo creator"
        assert asset["license"] == license_name
        assert asset["license_url"].startswith("https://creativecommons.org/")
    else:
        assert result is None


def test_manual_subtitle_layout_and_ass_escaping(tmp_path):
    path = tmp_path / "demo.ass"
    render_video.write_ass("Hello {demo}. Another sentence.", 4.0, path, "Demo", 64)
    text = path.read_text()
    assert "PlayResX: 1080" in text
    assert "Dialogue: 0,0:00:00.00,0:00:04.00,Title" in text
    assert r"\{demo\}" in text
    assert render_video.timestamp(61.25) == "00:01:01,250"


def test_local_render_generates_video_subtitles_and_credits(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    demo.main()
    monkeypatch.setattr(video.shutil, "which", lambda name: f"/demo/{name}")
    monkeypatch.setenv("TTS_BACKEND", "local")
    monkeypatch.setattr(video, "_commons_asset", lambda *args: None)
    calls = []

    def executable(command, **kwargs):
        from pathlib import Path

        calls.append(command)
        if command[0] == "espeak-ng":
            Path(command[command.index("-w") + 1]).write_bytes(b"a" * 1200)
        elif command[0] == "ffmpeg":
            Path(command[-1]).write_bytes(b"synthetic MP4")
        return subprocess.CompletedProcess(command, 0, "5.5\n")

    monkeypatch.setattr(video.subprocess, "run", executable)
    result = video.render_daily_video(data, day_stamp(), "Contoh observability lokal.")
    folder = data / "videos" / day_stamp()
    assert (folder / result["filename"]).exists()
    assert (folder / result["srt"]).exists()
    assert (folder / result["credits"]).exists()
    assert result["motion_cards"] == 1
    assert result["duration_seconds"] == 5.5
    assert all(command[0] != "python3" for command in calls)


def test_tts_timeout_becomes_actionable_render_error(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    demo.main()
    monkeypatch.setattr(video.shutil, "which", lambda name: f"/demo/{name}")

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 90)

    monkeypatch.setattr(video.subprocess, "run", timeout)
    with pytest.raises(video.VideoGenerationError, match="could not complete"):
        video.render_daily_video(data, day_stamp(), "Demo.")
