#!/usr/bin/env python3
"""Techbro & Tempo Digest - web viewer.
Reads JSON produced by scan.py / tempo.py / digest cron from /data (host mount)."""
import json, os, glob, datetime, re, threading
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
import httpx
from video_generation import VideoGenerationError, render_daily_video

app = FastAPI()
DATA_DIR = os.environ.get("DATA_DIR", "/data")
ADACODE_KEY = os.environ.get("ADACODE_API_KEY", "")
ADACODE_MODEL = os.environ.get("ADACODE_MODEL", "claude-sonnet-4-6")
ADACODE_BASE = "https://api.adacode.ai/v1/chat/completions"
TEMPLATE_DIR = os.environ.get(
    "TEMPLATE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)
TEMPLATES = Jinja2Templates(directory=TEMPLATE_DIR)
VIDEO_RENDER_ENABLED = os.environ.get("ENABLE_VIDEO_RENDER", "false").lower() in {"1", "true", "yes"}
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
VIDEO_RENDER_LOCK = threading.Lock()


def _latest(prefix):
    files = sorted(glob.glob(os.path.join(DATA_DIR, prefix, f"{prefix}_*.json")))
    if not files:
        return None
    try:
        return json.load(open(files[-1]))
    except Exception:
        return None


def _latest_topics():
    return _latest("topics")


def _today_prefix():
    return datetime.datetime.utcnow().strftime("%Y%m%d")


def _daily_dates():
    dates = []
    for path in glob.glob(os.path.join(DATA_DIR, "feed", "feed_*.json")):
        day = os.path.basename(path)[5:-5]
        if len(day) == 8 and day.isdigit():
            dates.append(day)
    return sorted(set(dates), reverse=True)


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _build_context():
    """Gabungkan semua data techbro + tempo dari digest terbaru jadi teks."""
    d = _latest("digest")
    if not d or not isinstance(d, dict):
        print("[CHAT-DEBUG] no digest data found", flush=True)
        return "(belum ada data digest)"
    try:
        # d sudah berupa dict (hasil json.load dari _latest)
        pass
    except Exception as e:
        print(f"[CHAT-DEBUG] error: {e}", flush=True)
        return "(gagal baca digest)"

    parts = []
    tb = d.get("techbro", {})
    parts.append("### TECHBRO / TWITTER")
    for c in tb.get("contributors", [])[:8]:
        parts.append(f"- @{c.get('user')}: {c.get('count')} tweet")
    for t in tb.get("themes", []):
        body = " ".join(t.get("body", []))
        parts.append(f"\n**{t.get('title')}**\n{t.get('summary','')}\n{body}")

    tp = d.get("tempo", {})
    # tempo & politics dihapus — fokus techbro only
    # topik hangat techbro (tracker)
    tp = _latest_topics()
    if tp and tp.get("topics"):
        parts.append("\n### TOPIK HANGAT TECHBRO (24 jam terakhir)")
        for t in tp["topics"]:
            parts.append(f"\n**{t.get('topic')}** ({t.get('count')} tweet): {t.get('summary','')}")
            if t.get("handles"):
                parts.append("  handles: " + ", ".join(t["handles"]))
    out = "\n".join(parts)
    print(f"[CHAT-DEBUG] context built, len={len(out)}", flush=True)
    return out


SYSTEM = (
    "Kamu asisten yang menjawab berdasarkan data milik Rafa dari Twitter (akun techbro) "
    "dan koran Tempo. Gunakan KONTEKS di bawah. Jika di luar konteks, jawab wawasan umum "
    "tapi sebutkan kalau tidak ada di data. Bahasa santai Indo (lo-gue). Jangan buat data "
    "yang tidak ada.\n\nKONTEKS DATA:\n"
)


@app.get("/")
def home(request: Request, day: str = None):
    return daily_page(request, day)


@app.get("/_home_old")
def home_old(request: Request):
    import glob
    all_digests = []
    for f in sorted(glob.glob(os.path.join(DATA_DIR, "digest", "digest_*.json"))):
        try:
            d = json.load(open(f))
            if d.get("techbro") and d["techbro"].get("themes"):
                all_digests.append(d)
        except:
            pass

    date = _today_prefix()
    feed = _latest("feed") or {"tweets": [], "techbro_tweets": 0,
                               "total_tweets": 0, "total_users": 0}
    tempo = _latest("tempo") or {"articles": [], "count": 0}
    news = _latest("news_monitor") or None

    by_author = {}
    for t in feed.get("tweets", []):
        if not t.get("is_techbro_id"):
            continue
        by_author.setdefault(t["user"], []).append(t)
    authors = []
    for u, ts in by_author.items():
        ts.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        authors.append({"user": u, "tweets": ts[:5], "count": len(ts)})
    authors.sort(key=lambda a: -a["count"])

    return TEMPLATES.TemplateResponse(request=request, name="index.html", context={
        "request": request,
        "date": date,
        "feed": feed,
        "tempo": tempo,
        "all_digests": all_digests,
        "authors": authors,
        "tempo_articles": tempo.get("articles", [])[:40],
        "pantauan": None,
        "topics": _latest_topics(),
        "news": news,
        "has_digest": len(all_digests) > 0,
    })


@app.get("/daily")
def daily_page(request: Request, day: str = None):
    dates = _daily_dates()
    selected = day if day in dates else (dates[0] if dates else None)
    feed = _load_json(os.path.join(DATA_DIR, "feed", f"feed_{selected}.json")) if selected else None
    topics = _load_json(os.path.join(DATA_DIR, "topics", f"topics_{selected}.json")) if selected else None
    draft = _load_json(os.path.join(DATA_DIR, "threads", f"threads_draft_{selected}.json")) if selected else None
    if selected and not draft:
        old_draft = os.path.join(DATA_DIR, "threads", f"threads_draft_{selected}.txt")
        try:
            with open(old_draft, encoding="utf-8") as fh:
                legacy_parts = [p.strip() for p in fh.read().split("\n\n---\n\n") if p.strip()]
            draft = {"status": "draft", "parts": [
                {"number": i, "text": part} for i, part in enumerate(legacy_parts, start=1)
            ]}
        except OSError:
            pass
    return TEMPLATES.TemplateResponse(request=request, name="daily.html", context={
        "request": request,
        "dates": dates,
        "selected_day": selected,
        "feed": feed or {},
        "topics": (topics or {}).get("topics", []),
        "draft": draft,
    })


@app.get("/api/daily/{day}/tweets")
def daily_tweets(
    day: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=40, ge=1, le=100),
    techbro_only: bool = False,
):
    if day not in _daily_dates():
        return JSONResponse({"error": "tanggal tidak ditemukan"}, status_code=404)
    feed = _load_json(os.path.join(DATA_DIR, "feed", f"feed_{day}.json")) or {}
    tweets = feed.get("tweets", [])
    if techbro_only:
        tweets = [tweet for tweet in tweets if tweet.get("is_techbro_id")]
    tweets = sorted(tweets, key=lambda tweet: tweet.get("created_at") or "", reverse=True)
    page = tweets[offset:offset + limit]
    next_offset = offset + len(page)
    return {
        "day": day,
        "offset": offset,
        "total": len(tweets),
        "has_more": next_offset < len(tweets),
        "next_offset": next_offset,
        "tweets": page,
    }


@app.post("/api/daily/{day}/video")
async def generate_daily_video(day: str, request: Request):
    if not VIDEO_RENDER_ENABLED:
        raise HTTPException(status_code=503, detail="Local video generation is disabled")
    if day not in _daily_dates():
        raise HTTPException(status_code=404, detail="Tanggal tidak ditemukan")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request JSON tidak valid")
    script = body.get("voiceover") if isinstance(body, dict) else None
    assets_dir = body.get("assets_dir") if isinstance(body, dict) else None
    if assets_dir is not None and not isinstance(assets_dir, str):
        raise HTTPException(status_code=422, detail="assets_dir harus string")
    if not isinstance(script, str) or not script.strip() or len(script) > 1800:
        raise HTTPException(status_code=422, detail="Naskah wajib diisi (maksimal 1.800 karakter)")
    if not VIDEO_RENDER_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Video lain sedang dirender; tunggu sampai selesai")
    try:
        result = await run_in_threadpool(
            render_daily_video, DATA_DIR, day, script, PEXELS_API_KEY, assets_dir
        )
    except VideoGenerationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        VIDEO_RENDER_LOCK.release()
    base = f"/api/daily/{day}/video/{result['filename']}"
    return {"ok": True, **result, "video_url": base,
            "subtitle_url": f"/api/daily/{day}/video/{result['srt']}",
            "credits_url": f"/api/daily/{day}/video/{result['credits']}"}


@app.get("/api/daily/{day}/video/{filename}")
def daily_video_file(day: str, filename: str):
    if day not in _daily_dates() or not re.fullmatch(
        rf"techbro-{re.escape(day)}-\d{{6}}-[a-f0-9]{{8}}\.(?:mp4|srt|credits\.txt)", filename
    ):
        raise HTTPException(status_code=404, detail="File video tidak ditemukan")
    path = os.path.join(DATA_DIR, "videos", day, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File video tidak ditemukan")
    media_type = "video/mp4" if filename.endswith(".mp4") else "text/plain"
    return FileResponse(path, media_type=media_type, filename=filename if not filename.endswith(".mp4") else None)


@app.get("/api/daily/{day}/videos")
def daily_videos(day: str):
    if day not in _daily_dates():
        raise HTTPException(status_code=404, detail="Tanggal tidak ditemukan")
    folder = os.path.join(DATA_DIR, "videos", day)
    items = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder), reverse=True):
            if re.fullmatch(rf"techbro-{day}-\d{{6}}-[a-f0-9]{{8}}\.mp4", name):
                items.append({"filename": name, "video_url": f"/api/daily/{day}/video/{name}"})
    return {"day": day, "videos": items}


@app.post("/api/chat")
async def chat(request: Request):
    if not ADACODE_KEY:
        return JSONResponse({"error": "adaCODE key belum di-set"}, status_code=500)
    body = await request.json()
    user_msg = (body.get("message") or "").strip()
    history = body.get("history", [])
    if not user_msg:
        return JSONResponse({"error": "pesan kosong"}, status_code=400)

    ctx = _build_context()
    messages = [{"role": "system", "content": SYSTEM + ctx}]
    for m in history[-12:]:
        if m.get("role") in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                ADACODE_BASE,
                headers={"Authorization": f"Bearer {ADACODE_KEY}",
                         "Content-Type": "application/json"},
                json={"model": ADACODE_MODEL, "messages": messages,
                      "max_tokens": 800, "temperature": 0.7},
            )
            r.raise_for_status()
            data = r.json()
            return {"reply": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return JSONResponse({"error": f"gagal call adaCODE: {e}"}, status_code=502)


@app.get("/health")
def health():
    return {"ok": True, "data_dir": DATA_DIR, "has_key": bool(ADACODE_KEY)}


def _load_all_topics():
    """Kumpulkan semua topics_*.json jadi list berurutan tanggal (lama->baru)."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "topics", "topics_*.json")))
    out = []
    for f in files:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        date = d.get("date") or os.path.basename(f).replace("topics_", "").replace(".json", "")
        topics = d.get("topics", [])
        if not topics:
            continue
        out.append({
            "date": date,
            "scanned": d.get("total_tweets_scanned"),
            "topics": topics,
        })
    out.sort(key=lambda x: x["date"])
    return out


@app.get("/topics-timeline")
def topics_timeline(request: Request):
    days = _load_all_topics()
    # build set topik unik buat legenda
    seen = {}
    for d in days:
        for t in d["topics"]:
            seen[t.get("topic", "")] = seen.get(t.get("topic", ""), 0) + t.get("count", 0)
    top_topics = sorted(seen.items(), key=lambda x: -x[1])[:12]
    return TEMPLATES.TemplateResponse(request=request, name="topics_timeline.html", context={
        "request": request,
        "days": days,
        "top_topics": top_topics,
        "total_days": len(days),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
