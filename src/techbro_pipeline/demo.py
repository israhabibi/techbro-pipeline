"""Offline synthetic pipeline; never reads credentials or calls external services."""

import datetime
from unittest.mock import patch

from techbro_pipeline import build_dataset, build_threads_draft, scan, topic_tracker
from techbro_pipeline.config import Settings, day_stamp, write_json


def main():
    settings = Settings.from_env()
    day = day_stamp()
    if (settings.data_dir / "feed" / f"feed_{day}.json").exists():
        raise SystemExit("Demo refuses to replace an existing feed; choose a separate DATA_DIR")
    now = datetime.datetime.now(datetime.UTC)
    tweet = {
        "text": "Belajar observability dan code review untuk software yang lebih andal.",
        "created_at": now.strftime("%a %b %d %H:%M:%S %z %Y"),
        "user_id_str": "demo-user-1",
    }
    timeline = {
        "globalObjects": {
            "tweets": {"demo-tweet-1": tweet},
            "users": {
                "demo-user-1": {
                    "screen_name": "fictional_builder",
                    "name": "Demo Engineer",
                    "location": "Jakarta",
                    "description": "Software engineer (synthetic demo)",
                }
            },
        }
    }
    topics = [
        {
            "topic": "Observability",
            "count": 1,
            "summary": "Akun fiktif membahas observability. Contoh ini memakai data sintetis.",
            "context": "Observability membantu menjelaskan keadaan aplikasi.",
            "value_added": "Analisis: pengamatan sistem membantu menemukan kegagalan lebih awal.",
            "handles": ["@fictional_builder"],
            "days": [now.strftime("%Y-%m-%d")],
        }
    ]
    with (
        patch.object(scan, "load_creds", return_value={}),
        patch.object(scan, "fetch_timeline", return_value=timeline),
        patch.object(topic_tracker, "extract_topics", return_value=topics),
    ):
        if scan.main(1):
            return 1
        write_json(
            settings.data_dir / "sources" / f"sources_{day}.json",
            {
                "date": day,
                "keywords": {"software": [{"title": "Synthetic demo headline"}]},
                "tempo": [],
                "demo": True,
            },
        )
        if topic_tracker.main():
            return 1
        build_threads_draft.main()
        build_dataset.build_tweets()
        build_dataset.build_topics()
        build_dataset.build_activity()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    log = [f"=== RUN {day} ==="]
    from techbro_pipeline.pipeline import STAGES

    for index, (_, label) in enumerate(STAGES, start=1):
        log.extend([f"=== [{index}/5] {label} ===", "[demo] synthetic stage completed"])
    log.append(f"=== DONE {now.isoformat()} ===")
    with (settings.data_dir / "pipeline.log").open("a", encoding="utf-8") as handle:
        handle.write("\n".join(log) + "\n")
    print(f"Demo artifacts: {settings.data_dir}; datasets: {settings.dataset_dir}")
    return 0
