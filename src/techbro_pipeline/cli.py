"""Console commands; import stage implementations only when selected."""

import argparse
import importlib
import os
import sys
from pathlib import Path

STAGES = {
    "scan": "scan",
    "sources": "sources",
    "topics": "topic_tracker",
    "threads": "build_threads_draft",
    "dataset": "build_dataset",
    "render": "render_video",
    "demo": "demo",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Techbro pipeline and dashboard")
    parser.add_argument("--env-file", type=Path, help="Explicit local environment file")
    parser.add_argument("command", choices=[*STAGES, "serve", "pipeline"])
    args, remaining = parser.parse_known_args(argv)
    if args.env_file:
        if not args.env_file.is_file():
            parser.error("environment file does not exist")
        from dotenv import load_dotenv

        load_dotenv(args.env_file, override=False)
    if args.command == "serve":
        import uvicorn

        server = argparse.ArgumentParser(prog="techbro serve")
        server.add_argument("--host", default="127.0.0.1")
        server.add_argument("--port", type=int, default=8000)
        options = server.parse_args(remaining)
        uvicorn.run("techbro_pipeline.web.main:app", host=options.host, port=options.port)
        return 0
    if args.command == "pipeline":
        if remaining:
            parser.error("pipeline does not accept extra arguments")
        from techbro_pipeline.pipeline import run

        return run()
    module = importlib.import_module(f"techbro_pipeline.{STAGES[args.command]}")
    previous = sys.argv
    try:
        sys.argv = [f"techbro {args.command}", *remaining]
        if args.command == "scan":
            scan = argparse.ArgumentParser(prog="techbro scan")
            scan.add_argument("pages", nargs="?", type=int, default=os.getenv("SCAN_PAGES", "3"))
            options = scan.parse_args(remaining)
            if not 1 <= options.pages <= 100:
                scan.error("pages must be between 1 and 100")
            return module.main(options.pages) or 0
        return module.main() or 0
    finally:
        sys.argv = previous


if __name__ == "__main__":
    raise SystemExit(main())
