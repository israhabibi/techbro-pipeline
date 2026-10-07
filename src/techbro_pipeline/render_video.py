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
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
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


def caption_width(font_size):
    """Approximate characters per line on the 1080-wide canvas for DejaVu Sans.

    Average advance width is ~0.55em, so a 64px face fits ~28 characters in the
    ~1000px usable area. Keeps wrapping consistent with the rendered font size.
    """
    usable = 1080 - 2 * max(40, round(font_size * 0.9))
    return max(14, int(usable / (font_size * 0.55)))


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
    return ["\n".join(lines[i : i + 2]) for i in range(0, len(lines), 2)]


def write_srt(text, duration, destination, width=42):
    units = []
    for sentence in sentences(text):
        cards = wrap_caption(sentence, width)
        weights = [max(1, len(card.split())) for card in cards]
        for card, weight in zip(cards, weights, strict=True):
            units.append((card, weight))
    total_weight = sum(weight for _, weight in units) or 1
    elapsed, blocks = 0.0, []
    for number, (caption, weight) in enumerate(units, start=1):
        end = duration if number == len(units) else elapsed + duration * weight / total_weight
        blocks.append(f"{number}\n{timestamp(elapsed)} --> {timestamp(end)}\n{caption}\n")
        elapsed = end
    destination.write_text("\n".join(blocks), encoding="utf-8")


def ass_time(seconds):
    centiseconds = max(0, round(seconds * 100))
    hours, centiseconds = divmod(centiseconds, 3_600_000)
    minutes, centiseconds = divmod(centiseconds, 60_000)
    secs, centiseconds = divmod(centiseconds, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def escape_ass(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


# Style tokens matched to the reference frame analysis (589x1280 sample):
# - Title: mid-gray text (~RGB 128,128,128) in the upper band y=128-256 (~10-20%).
# - Caption: bold white text on a sepia/brown box (~RGB 128,112,96) at y=1024-1088
#   (~80-85%), i.e. MarginV ~288px on the 1920px canvas.
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,DejaVu Sans,{title_size},&H00808080,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,80,80,{title_margin},1
Style: Caption,DejaVu Sans,{font_size},&H00FFFFFF,&H00FFFFFF,&HC0000000,&H00607080,1,0,0,0,100,100,0,0,3,{caption_pad},0,2,70,70,{caption_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(text, duration, destination, title, font_size):
    """Styled ASS: gray title pinned to the upper band, boxed captions near the
    lower third — mirroring the reference Shorts layout instead of centered subs."""
    lines = [
        ASS_HEADER.format(
            title_size=max(40, round(font_size * 0.85)),
            title_margin=round(1920 * 0.10),
            font_size=font_size,
            caption_pad=max(6, round(font_size / 8)),
            caption_margin=384,
        )
    ]
    if title:
        lines.append(
            f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Title,,0,0,0,,{escape_ass(title)}"
        )
    # First pass: collect caption cards with placeholder timing.
    caption_cards = []
    for sentence in sentences(text):
        for card in wrap_caption(sentence, caption_width(font_size)):
            caption_cards.append(escape_ass(card.replace(chr(10), chr(92) + "N")))
    # Second pass: assign each card an equal time slice with correct field
    # order (Layer,Start,End,Style,...).
    slice_duration = duration / max(1, len(caption_cards))
    for index, card_text in enumerate(caption_cards):
        start = ass_time(index * slice_duration)
        end = ass_time(
            duration if index == len(caption_cards) - 1 else (index + 1) * slice_duration
        )
        lines.append(f"Dialogue: 0,{start},{end},Caption,,0,0,0,,{card_text}")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def script_groups(text, scene_count):
    chunks = re.split(r"(?=Topik\s+\d+\s*,)", text, flags=re.IGNORECASE)
    intro, topic_chunks = chunks[0], chunks[1:]
    if len(topic_chunks) != scene_count:
        return [text] * scene_count
    topic_chunks[0] = intro + topic_chunks[0]
    return topic_chunks


def escape_filter_path(path):
    return (
        str(path.resolve())
        .replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan", required=True, type=Path, help="JSON downloaded from Studio video harian"
    )
    parser.add_argument(
        "--assets-dir", required=True, type=Path, help="Contains scene-01.mp4, scene-02.mp4, ..."
    )
    parser.add_argument(
        "--audio", required=True, type=Path, help="TTS narration file (WAV/MP3/M4A)"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New MP4 output path; existing files are not overwritten",
    )
    parser.add_argument(
        "--title",
        default="",
        help="Static title shown in the upper band for the whole video (techbro overlay style)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=64,
        help="Subtitle font size in pixels for the 1080x1920 canvas (default: 64)",
    )
    parser.add_argument(
        "--margin-v",
        type=int,
        default=420,
        help="Subtitle bottom margin in pixels; larger keeps captions higher up (default: 420)",
    )
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
        options = [
            args.assets_dir / f"scene-{number:02}{suffix}"
            for suffix in (".mp4", ".mov", ".m4v", ".webm", ".mkv")
        ]
        clip = next((candidate for candidate in options if candidate.is_file()), None)
        if clip is None:
            parser.error(
                f"scene {number}: download the chosen clip as scene-{number:02}.mp4 (or a supported video format)"
            )
        clips.append((scene, clip))

    args.output = args.output.resolve()
    srt_path = args.output.with_suffix(".srt")
    ass_path = args.output.with_suffix(".ass")
    credits_path = args.output.with_suffix(".credits.txt")
    if any(path.exists() for path in (args.output, srt_path, ass_path, credits_path)):
        parser.error(
            "output MP4, ASS, SRT, or credits file already exists; choose a new output name"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(args.audio)
    if duration <= 0:
        parser.error("TTS audio has no duration")

    groups = script_groups(narration, len(clips))
    weights = [max(1, len(group.split())) for group in groups]
    total_weight = sum(weights)
    clip_durations = [duration * weight / total_weight for weight in weights]
    write_srt(narration, duration, srt_path, caption_width(args.font_size))
    write_ass(narration, duration, ass_path, args.title, args.font_size)

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
    srt_filter = escape_filter_path(ass_path)
    # Styled ASS (techbro overlay): gray title in the upper band, bold white
    # captions on a sepia box near the lower third — see write_ass().
    filters.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=0,subtitles='{srt_filter}'[video]")
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[video]",
            "-map",
            f"{audio_index}:a:0",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "25",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(args.output),
        ]
    )
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        srt_path.unlink(missing_ok=True)
        ass_path.unlink(missing_ok=True)
        parser.error(
            f"FFmpeg render failed (exit {exc.returncode}); verify that clips include video and FFmpeg has libass"
        )

    credits = ["Asset credits — verify these match each source page before publishing."]
    for scene, _ in clips:
        asset = scene["asset"]
        credits.append(
            f"Scene {scene.get('scene')}: {scene.get('topic')} | {asset['creator']} | {asset['license']} | {asset['assetUrl']}"
        )
    credits.append(
        "AI disclosure: Rangkuman ini disusun dengan bantuan AI dari obrolan publik di X."
    )
    credits_path.write_text("\n".join(credits) + "\n", encoding="utf-8")
    print(f"Rendered: {args.output}")
    print(f"Subtitles: {srt_path}")
    print(f"Styled overlay: {ass_path}")
    print(f"Credits: {credits_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
