---
name: techbro-digest-pipeline
description: 'Maintain the Techbro Twitter digest pipeline on VPS: cron job, digest JSON format (PENDEK 6 poin), web deploy via docker compose. Used when user says "digest kepanjangan", "ubah format web", "buat pendek", "ilangin tempo".'
---

# Techbro Digest Pipeline

Techbro Twitter digest pipeline running on VPS /home/isra_habibi/techbro.

## Data Files

- `data/feed_YYYYMMDD.json` — raw tweets from Twitter scan
- `data/digest_YYYYMMDD.json` — structured digest with TL;DR + 6-point themes (PENDEK)
- `data/topics_*.json` — topic tracker (14-day window)

## Digest JSON Format (PENDEK — 6 poin, bukan naratif)

```json
{
  "date": "20260926",
  "tldr": "1 baris ringkasan di atas.",
  "techbro": {
    "contributors": [{"user": "handle", "count": N}],
    "themes": [
      {"title": "Judul poin", "summary": "1 kalimat", "body": ["1-2 kalimat doang"]}
    ]
  }
}
```

CRITICAL: body harus 1-2 kalimat PENDEK, bukan paragraf naratif. Tiap theme = 1 poin thread.

## Web Layout (top to bottom)

1. TL;DR (1 baris, dari digest.tldr)
2. Thread Harian Techbro — per theme: title + summary + body (pendek)
3. Tracker Topik (14 hari)

No Tempo, no politics, no Prabowo, no adaCODE/chat AI.

## Cron Job

- `86d0c82fb6f6` — Techbro Daily Digest (X Thread)
- Schedule: `0 1 * * *` (01:00 UTC / 08:00 WIB)
- Model: `deepseek-v4-flash-0731:netra` via `custom:ai.sumopod.com`
- Pinned — won't skip on model change
- Format: thread-style (3-6 tweets, ~200-240 chars each)
- Content: ALL tweets in feed, filter by CONTENT not is_techbro_id flag
- NO politics, NO Tempo, NO general news

## Deploy Web

```bash
cd /home/isra_habibi/techbro
docker compose up -d --build digest
```

## To Overwrite digest.json Manually (short format)

```bash
cd /home/isra_habibi/techbro && python3 -c "
import json, collections
feed = json.load(open('data/feed_YYYYMMDD.json'))
tb = [t for t in feed['tweets'] if t.get('is_techbro_id')]
cnt = collections.Counter(t['user'] for t in tb)
d = {
  'date': 'YYYYMMDD',
  'tldr': '1 baris ringkasan',
  'techbro': {
    'contributors': [{'user':u,'count':c} for u,c in cnt.most_common(8)],
    'themes': [
      {'title':'Poin 1','summary':'1 kalimat','body':['1-2 kalimat']},
    ]
  }
}
json.dump(d, open('data/digest_YYYYMMDD.json','w'), indent=2)
"
docker compose up -d --build digest
```

## Pitfalls & User Preferences

- User ingin format PENDEK (6 poin, bukan narasi 4-5 paragraf)
- No Tempo, no politics — techbro only
- Filter content by topic (AI/coding/startup/engineering), NOT by is_techbro_id flag
- Akun @BukanYahya tweet tech content but not flagged as techbro_id — solved by konten-based filtering
- Chat AI (adaCODE) harus dihapus dari template
- web harus selalu rebuild dengan docker compose up -d --build digest setelah ganti template/data
