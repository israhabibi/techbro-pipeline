"""Clone a pushed revision, install locked dependencies, and check it independently."""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from smoke import clean_environment


def run(command, folder, env):
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, cwd=folder, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="https://github.com/israhabibi/techbro-pipeline.git")
    parser.add_argument(
        "--ref", default=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    )
    parser.add_argument("--keep", action="store_true", help="Keep the checkout for inspection")
    args = parser.parse_args()
    folder = Path(tempfile.mkdtemp(prefix="techbro-reproduce-"))
    env = clean_environment()
    env["UV_PROJECT_ENVIRONMENT"] = str(folder / ".venv")
    success = False
    try:
        run(["git", "clone", "--quiet", args.source, str(folder)], Path.cwd(), env)
        run(["git", "checkout", "--quiet", args.ref], folder, env)
        run(["uv", "sync", "--locked"], folder, env)
        run(["npm", "ci"], folder, env)
        run(["make", "check"], folder, env)
        run(["uv", "run", "--locked", "python", "scripts/smoke.py"], folder, env)
        run(["make", "audit"], folder, env)
        run(["npm", "audit", "--audit-level=high"], folder, env)
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=folder, text=True)
        if dirty:
            raise RuntimeError("Verification unexpectedly modified tracked source: " + dirty)
        success = True
        print(f"Clean checkout verification PASSED for {args.ref}")
        return 0
    finally:
        if args.keep or not success:
            print(f"Checkout retained at {folder}")
        else:
            shutil.rmtree(folder)


if __name__ == "__main__":
    raise SystemExit(main())
