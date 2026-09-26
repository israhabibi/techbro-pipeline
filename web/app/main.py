#!/usr/bin/env python3
"""Techbro & Tempo Digest - web viewer.
Reads JSON produced by scan.py / tempo.py / digest cron from /data (host mount)."""
import json, os, glob, datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()
DATA_DIR = os.environ.get("DATA_DIR", "/data")
ADACODE_KEY = os.environ.get("ADACODE_API_KEY", "")
ADACODE_MODEL = os.environ.get("ADACODE_MODEL", "claude-sonnet-4-6")
ADACODE_BASE = "https://api.adacode.ai/v1/chat/completions"
TEMPLATES = Jinja2Templates(directory="/app/templates")


def _latest(prefix):
    files = sorted(glob.glob(os.path.join(DATA_DIR, f"{prefix}_*.json")))
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
        parts.append("\n### TOPIK HANGAT TECHBRO (14 hari terakhir)")
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
def home(request: Request):
    date = _today_prefix()
    feed = _latest("feed") or {"tweets": [], "techbro_tweets": 0,
                               "total_tweets": 0, "total_users": 0}
    tempo = _latest("tempo") or {"articles": [], "count": 0}
    digest = _latest("digest") or None
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
        "digest": digest,
        "authors": authors,
        "tempo_articles": tempo.get("articles", [])[:40],
        "has_digest": digest is not None,
        "pantauan": digest.get("pantauan") if digest else None,
        "topics": _latest_topics(),
        "news": news,
    })


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
    files = sorted(glob.glob(os.path.join(DATA_DIR, "topics_*.json")))
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
