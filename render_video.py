#!/usr/bin/env python3
"""Assemble a reviewed daily video plan, local clips, and TTS audio with FFmpeg."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def timestamp(seconds):
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def wrap_caption(text, width=42):
    words, lines, current = text.split(), [], ""
    for word in words:
        if current and len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    # Keep captions readable: split any long sentence into subtitle cards.
    return ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]


def write_srt(text, duration, destination):
    units = []
    for sentence in sentences(text):
        words = sentence.split()
        cards = wrap_caption(sentence)
        weights = [max(1, len(card.split())) for card in cards]
        for card, weight in zip(cards, weights):
            units.append((card, weight))
    total_weight = sum(weight for _, weight in units) or 1
    elapsed, blocks = 0.0, []
    for number, (caption, weight) in enumerate(units, start=1):
        end = duration if number == len(units) else elapsed + duration * weight / total_weight
        blocks.append(f"{number}\n{timestamp(elapsed)} --> {timestamp(end)}\n{caption}\n")
        elapsed = end
    destination.write_text("\n".join(blocks), encoding="utf-8")


def script_groups(text, scene_count):
    chunks = re.split(r"(?=Topik\s+\d+\s*,)", text, flags=re.IGNORECASE)
    intro, topic_chunks = chunks[0], chunks[1:]
    if len(topic_chunks) != scene_count:
        return [text] * scene_count
    topic_chunks[0] = intro + topic_chunks[0]
    return topic_chunks


def escape_filter_path(path):
    return str(path.resolve()).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path, help="JSON downloaded from Studio video harian")
    parser.add_argument("--assets-dir", required=True, type=Path, help="Contains scene-01.mp4, scene-02.mp4, ...")
    parser.add_argument("--audio", required=True, type=Path, help="TTS narration file (WAV/MP3/M4A)")
    parser.add_argument("--output", required=True, type=Path, help="New MP4 output path; existing files are not overwritten")
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.error("ffmpeg and ffprobe must be installed")
    for path in (args.plan, args.audio):
        if not path.is_file():
            parser.error(f"file not found: {path}")
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.error(f"cannot read plan JSON: {exc}")
    scenes = plan.get("scenes") or []
    narration = (plan.get("voiceover") or "").strip()
    if not scenes or not narration:
        parser.error("plan must contain at least one scene and a voiceover script")

    clips = []
    for scene in scenes:
        number = int(scene.get("scene", len(clips) + 1))
        asset = scene.get("asset") or {}
        if asset.get("checked") is not True:
            parser.error(f"scene {number}: confirm asset usage/license in the UI before rendering")
        for field in ("assetUrl", "creator", "license"):
            if not asset.get(field):
                parser.error(f"scene {number}: fill in asset URL, creator, and license in the UI")
        options = [args.assets_dir / f"scene-{number:02}{suffix}"
                   for suffix in (".mp4", ".mov", ".m4v", ".webm", ".mkv")]
        clip = next((candidate for candidate in options if candidate.is_file()), None)
        if clip is None:
            parser.error(f"scene {number}: download the chosen clip as scene-{number:02}.mp4 (or a supported video format)")
        clips.append((scene, clip))

    args.output = args.output.resolve()
    srt_path = args.output.with_suffix(".srt")
    credits_path = args.output.with_suffix(".credits.txt")
    if any(path.exists() for path in (args.output, srt_path, credits_path)):
        parser.error("output MP4, SRT, or credits file already exists; choose a new output name")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(args.audio)
    if duration <= 0:
        parser.error("TTS audio has no duration")

    groups = script_groups(narration, len(clips))
    weights = [max(1, len(group.split())) for group in groups]
    total_weight = sum(weights)
    clip_durations = [duration * weight / total_weight for weight in weights]
    write_srt(narration, duration, srt_path)

    command = ["ffmpeg", "-hide_banner", "-loglevel", "warning"]
    for _, clip in clips:
        command.extend(["-stream_loop", "-1", "-i", str(clip)])
    audio_index = len(clips)
    command.extend(["-i", str(args.audio)])
    filters = []
    for index, clip_duration in enumerate(clip_durations):
        filters.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,fps=30,setsar=1,trim=duration={clip_duration:.3f},"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
    concat_inputs = "".join(f"[v{index}]" for index in range(len(clips)))
    srt_filter = escape_filter_path(srt_path)
    filters.append(
        f"{concat_inputs}concat=n={len(clips)}:v=1:a=0,"
        f"subtitles='{srt_filter}':force_style='FontName=DejaVu Sans,FontSize=18,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=1,"
        "Outline=2,Shadow=1,Alignment=2,MarginV=150'[video]"
    )
    command.extend(["-filter_complex", ";".join(filters), "-map", "[video]",
                    "-map", f"{audio_index}:a:0", "-t", f"{duration:.3f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(args.output)])
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        srt_path.unlink(missing_ok=True)
        parser.error(f"FFmpeg render failed (exit {exc.returncode}); verify that clips include video and FFmpeg has libass")

    credits = ["Asset credits — verify these match each source page before publishing."]
    for scene, _ in clips:
        asset = scene["asset"]
        credits.append(f"Scene {scene.get('scene')}: {scene.get('topic')} | {asset['creator']} | {asset['license']} | {asset['assetUrl']}")
    credits.append("AI disclosure: Rangkuman ini disusun dengan bantuan AI dari obrolan publik di X.")
    credits_path.write_text("\n".join(credits) + "\n", encoding="utf-8")
    print(f"Rendered: {args.output}")
    print(f"Subtitles: {srt_path}")
    print(f"Credits: {credits_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
