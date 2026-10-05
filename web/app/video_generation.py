"""On-demand local TTS + FFmpeg video assembly for a daily topic draft."""
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Jakarta")
PEXELS_API = "https://api.pexels.com/v1/videos/search"
MAX_CLIP_BYTES = 24 * 1024 * 1024
MAX_DAILY_RENDERS = 3
MAX_TOTAL_RENDERS = 30


class VideoGenerationError(RuntimeError):
    pass


def _json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _safe_filter_path(path):
    return str(path.resolve()).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")


def _sentence_units(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _caption_lines(text, width=34):
    lines, current = [], ""
    for word in text.split():
        if current and len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


def _srt_time(seconds):
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _write_srt(text, duration, destination):
    cards = []
    for sentence in _sentence_units(text):
        for caption in _caption_lines(sentence):
            cards.append((caption, max(1, len(caption.split()))))
    total = sum(weight for _, weight in cards) or 1
    elapsed, blocks = 0.0, []
    for index, (caption, weight) in enumerate(cards, start=1):
        end = duration if index == len(cards) else elapsed + duration * weight / total
        blocks.append(f"{index}\n{_srt_time(elapsed)} --> {_srt_time(end)}\n{caption}\n")
        elapsed = end
    destination.write_text("\n".join(blocks), encoding="utf-8")


def _search_terms(topic):
    name = (topic or "").lower()
    if "agent" in name or "video" in name:
        return "video editing computer creative studio vertical"
    if "rust" in name or "swift" in name:
        return "software developer coding computer vertical"
    if "observability" in name:
        return "server monitoring data center computer vertical"
    if "voice" in name or "elevenlabs" in name:
        return "microphone sound recording studio vertical"
    return f"technology computer software vertical {topic}"


def _pexels_asset(query, api_key, destination):
    if not api_key:
        return None
    params = urllib.parse.urlencode({"query": query, "orientation": "portrait", "per_page": 5, "size": "medium"})
    req = urllib.request.Request(f"{PEXELS_API}?{params}", headers={"Authorization": api_key, "User-Agent": "TechbroDailyVideo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        videos = payload.get("videos") or []
        for video in videos:
            files = [f for f in video.get("video_files", [])
                     if f.get("file_type") == "video/mp4" and f.get("link")]
            files.sort(key=lambda f: (f.get("width") or 99999, f.get("height") or 99999))
            for item in files:
                parsed = urllib.parse.urlparse(item["link"])
                if parsed.scheme != "https" or parsed.hostname not in {"player.vimeo.com", "videos.pexels.com"}:
                    continue
                download = urllib.request.Request(item["link"], headers={"User-Agent": "TechbroDailyVideo/1.0"})
                with urllib.request.urlopen(download, timeout=25) as media:
                    if int(media.headers.get("Content-Length", "0") or 0) > MAX_CLIP_BYTES:
                        continue
                    data = media.read(MAX_CLIP_BYTES + 1)
                if len(data) > MAX_CLIP_BYTES or b"ftyp" not in data[:32]:
                    continue
                destination.write_bytes(data)
                user = video.get("user") or {}
                return {
                    "type": "pexels",
                    "source": video.get("url", "https://www.pexels.com/"),
                    "creator": user.get("name", "Pexels contributor"),
                    "creator_url": user.get("url", "https://www.pexels.com/"),
                    "license": "Pexels License — review before publishing",
                }
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    return None


def _group_voiceover(script, count):
    parts = re.split(r"(?=Topik\s+\d+\s*,)", script, flags=re.IGNORECASE)
    intro, groups = parts[0], parts[1:]
    if len(groups) != count:
        return [script] * count
    groups[0] = intro + groups[0]
    return groups


def _render_ffmpeg(clips, titles, voice_path, srt_path, duration, output):
    command, filters = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"], []
    # durations are distributed by narration chunk size, passed alongside titles
    chunks = titles["_groups"]
    lengths = [max(1, len(text.split())) for text in chunks]
    total = sum(lengths)
    durations = [duration * size / total for size in lengths]
    input_index = 0
    for index, (clip, title) in enumerate(zip(clips, titles["_titles"])):
        if clip:
            command.extend(["-stream_loop", "-1", "-i", str(clip)])
        else:
            color = ["0x11251f", "0x181d33", "0x2b1d2d"][index % 3]
            command.extend(["-f", "lavfi", "-i", f"color=c={color}:s=720x1280:r=25:d={durations[index]:.3f}"])
        title_path = Path(titles["_title_files"][index])
        title_filter_path = _safe_filter_path(title_path)
        common = (
            "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,"
            "fps=25,setsar=1,"
            f"drawbox=x='mod(t*70,720)':y=0:w=240:h=1280:color=0x44d7a8@0.10:t=fill,"
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile='{title_filter_path}':"
            "fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=16:"
            "box=1:boxcolor=0x07110f@0.48:boxborderw=32,"
            f"trim=duration={durations[index]:.3f},setpts=PTS-STARTPTS"
        )
        filters.append(f"[{input_index}:v]{common}[v{index}]")
        input_index += 1
    audio_index = input_index
    command.extend(["-i", str(voice_path)])
    joined = "".join(f"[v{i}]" for i in range(len(clips)))
    srt = _safe_filter_path(srt_path)
    filters.append(
        f"{joined}concat=n={len(clips)}:v=1:a=0,"
        f"subtitles='{srt}':force_style='PlayResX=720,PlayResY=1280,FontName=DejaVu Sans,FontSize=32,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=1,"
        "Outline=2,Shadow=1,Alignment=2,MarginV=110'[video]"
    )
    command.extend(["-filter_complex", ";".join(filters), "-map", "[video]", "-map", f"{audio_index}:a:0",
                    "-t", f"{duration:.3f}", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(output)])
    subprocess.run(command, check=True, timeout=300)


def render_daily_video(data_dir, day, script, pexels_key=""):
    if not re.fullmatch(r"\d{8}", day):
        raise VideoGenerationError("Format tanggal tidak valid")
    script = re.sub(r"\s+", " ", (script or "")).strip()
    if not script or len(script) > 1800:
        raise VideoGenerationError("Naskah kosong atau terlalu panjang (maksimal 1.800 karakter)")
    for executable in ("espeak-ng", "ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise VideoGenerationError(f"Dependensi lokal belum terpasang: {executable}")

    base = Path(data_dir)
    draft = _json_file(base / f"threads_draft_{day}.json")
    topics_file = _json_file(base / f"topics_{day}.json")
    topic_map = {t.get("topic"): t for t in topics_file.get("topics", [])}
    selected = [p.get("topic") for p in draft.get("parts", []) if p.get("kind") == "topic"][:3]
    topics = [topic_map[name] for name in selected if name in topic_map]
    if not topics:
        raise VideoGenerationError("Tidak ada topik harian untuk membuat storyboard")

    output_dir = base / "videos" / day
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(output_dir.glob("techbro-*.mp4"))
    if len(existing) >= MAX_DAILY_RENDERS:
        raise VideoGenerationError("Batas 3 render per hari tercapai")
    if len(list((base / "videos").glob("*/techbro-*.mp4"))) >= MAX_TOTAL_RENDERS:
        raise VideoGenerationError("Penyimpanan penuh (maksimal 30 video); pindahkan/hapus video lama terlebih dahulu")
    stamp = dt.datetime.now(TZ).strftime("%H%M%S")
    suffix = os.urandom(4).hex()
    stem = f"techbro-{day}-{stamp}-{suffix}"
    output = output_dir / f"{stem}.mp4"
    srt_path = output_dir / f"{stem}.srt"
    credits_path = output_dir / f"{stem}.credits.txt"

    with tempfile.TemporaryDirectory(prefix="techbro-video-") as temp_name:
        temp = Path(temp_name)
        voice_path = temp / "voice.wav"
        text = subprocess.run(["espeak-ng", "-v", "id", "-s", "158", "-w", str(voice_path), "--stdin"],
                              input=script, text=True, capture_output=True, timeout=90)
        if text.returncode or not voice_path.exists() or voice_path.stat().st_size < 1000:
            raise VideoGenerationError("TTS lokal gagal membuat audio Bahasa Indonesia")
        try:
            duration = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)],
                                            check=True, capture_output=True, text=True, timeout=10).stdout.strip())
        except (ValueError, subprocess.SubprocessError) as exc:
            raise VideoGenerationError("Durasi audio TTS tidak bisa dibaca") from exc
        if duration > 100:
            raise VideoGenerationError("Audio lebih dari 100 detik; pendekkan naskah")

        script_groups = _group_voiceover(script, len(topics))
        title_files, clips, credits = [], [], []
        for index, topic in enumerate(topics, start=1):
            title_file = temp / f"title-{index}.txt"
            title = topic.get("topic") or f"Topik {index}"
            title_file.write_text(f"OBROLAN TECHBRO\n\n{title}", encoding="utf-8")
            title_files.append(title_file)
            downloaded = temp / f"clip-{index}.mp4"
            asset = _pexels_asset(_search_terms(title), pexels_key, downloaded)
            if asset:
                clips.append(downloaded)
                asset["topic"] = title
                credits.append(asset)
            else:
                clips.append(None)
                credits.append({"type": "generated", "topic": title,
                                "source": "Motion-card dibuat lokal dengan FFmpeg; tidak memakai footage eksternal."})

        subtitles = _sentence_units(script)
        _write_srt(script, duration, srt_path)
        title_config = {"_groups": script_groups, "_titles": [t.get("topic") or f"Topik {i+1}" for i, t in enumerate(topics)],
                        "_title_files": title_files}
        try:
            _render_ffmpeg(clips, title_config, voice_path, srt_path, duration, output)
        except (subprocess.SubprocessError, OSError) as exc:
            srt_path.unlink(missing_ok=True)
            output.unlink(missing_ok=True)
            raise VideoGenerationError(f"FFmpeg gagal merender video: {exc}") from exc

    credits_path.write_text(json.dumps({"date": day, "assets": credits,
                                       "disclaimer": "Naskah dibuat dengan bantuan AI. Voice-over disintesis lokal."},
                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"filename": output.name, "srt": srt_path.name, "credits": credits_path.name,
            "duration_seconds": round(duration, 1), "pexels_used": sum(a["type"] == "pexels" for a in credits),
            "motion_cards": sum(a["type"] == "generated" for a in credits)}
