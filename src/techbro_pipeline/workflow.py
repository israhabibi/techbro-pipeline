"""Send Techbro drafts to the separately installed, review-gated ai-workflow CLI."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from techbro_pipeline.config import Settings, day_stamp, write_json
from techbro_pipeline.meta import ThreadsError, read_draft, validate_day


class WorkflowError(Exception):
    """A diagnostic that contains no credentials or raw subprocess output."""


def enabled():
    return os.getenv("AI_WORKFLOW_AUTO_ENQUEUE", "false").lower() in {"1", "true", "yes"}


def home():
    value = os.getenv("AI_WORKFLOW_HOME")
    return (
        Path(value).expanduser().resolve() if value else Settings.from_env().data_dir / "workflow"
    )


def account_name():
    return os.getenv("AI_WORKFLOW_ACCOUNT", "techbro-threads")


def check_publishers():
    if any(
        os.getenv(name, "false").lower() in {"1", "true", "yes"}
        for name in ("THREADS_AUTO_PUBLISH", "REPLIZ_AUTO_SCHEDULE")
    ):
        raise WorkflowError(
            "disable THREADS_AUTO_PUBLISH and REPLIZ_AUTO_SCHEDULE before using ai-workflow"
        )


def invoke(*arguments):
    executable = os.getenv("AI_WORKFLOW_EXECUTABLE", "ai-workflow")
    try:
        result = subprocess.run(
            [executable, "--home", str(home()), *map(str, arguments)],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise WorkflowError("ai-workflow could not run; check AI_WORKFLOW_EXECUTABLE") from None
    if result.returncode:
        # The executable is externally configured; never echo its raw output.
        raise WorkflowError(
            "ai-workflow rejected the operation; check the draft, account configuration and job status"
        )
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise WorkflowError("ai-workflow returned an invalid JSON result") from None


def setup(provider):
    check_publishers()
    name = account_name()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise WorkflowError("AI_WORKFLOW_ACCOUNT must be an account name")
    user_id = (
        "demo"
        if provider == "mock"
        else os.getenv("REPLIZ_ACCOUNT_ID" if provider == "repliz" else "THREADS_USER_ID", "")
    )
    if not re.fullmatch(r"[A-Za-z0-9_.~-]+", user_id):
        raise WorkflowError("configure the explicit Threads user ID or Repliz account ID first")
    account = {"name": name, "platform": "threads", "provider": provider, "user_id": user_id}
    if provider == "native":
        account["token_env"] = "THREADS_ACCESS_TOKEN"
    document = {"schema_version": 1, "accounts": [account]}
    directory = home()
    path = directory / "workspace.json"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise WorkflowError(
                "existing workflow workspace is invalid; inspect it first"
            ) from None
        if existing != document:
            raise WorkflowError("workflow workspace already exists with different account settings")
    else:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        (directory / "assets").mkdir(exist_ok=True, mode=0o700)
        write_json(path, document)
        path.chmod(0o600)
    invoke("jobs")
    return {"home": str(directory), "account": name, "provider": provider}


def check_workspace():
    try:
        document = json.loads((home() / "workspace.json").read_text(encoding="utf-8"))
        accounts = document["accounts"]
        if not isinstance(accounts, list) or not any(
            isinstance(account, dict)
            and account.get("name") == account_name()
            and account.get("platform") == "threads"
            and account.get("provider") in ("native", "repliz", "mock")
            for account in accounts
        ):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise WorkflowError("run techbro workflow setup for the selected account first") from None


def check_legacy_receipts(day):
    data = Settings.from_env().data_dir
    for folder, prefix in (("meta", "publish"), ("repliz", "schedule")):
        if any((data / folder).glob(f"{prefix}_{day}_*.json")):
            raise WorkflowError(
                "this date has a legacy publishing receipt; inspect it before migrating to avoid reposting"
            )


def draft_operation(command, day, *, key=None, at=None):
    check_publishers()
    check_workspace()
    try:
        validate_day(day)
        texts = read_draft(day)
    except ThreadsError as exc:
        raise WorkflowError(str(exc)) from None
    if command == "enqueue":
        check_legacy_receipts(day)
    # Capture the exact validated parts; changes to the source during import cannot
    # switch the date or content that is previewed/enqueued.
    try:
        with tempfile.TemporaryDirectory(prefix="draft-", dir=home()) as temporary:
            source = Path(temporary) / "source.json"
            post = Path(temporary) / "post.json"
            write_json(source, {"parts": [{"text": text} for text in texts]})
            invoke(
                "import",
                "threads-draft",
                source,
                "--project",
                "techbro",
                "--key",
                key or f"daily-{day}",
                "--output",
                post,
            )
            arguments = [command, post, "--account", account_name()]
            if at:
                arguments.extend(("--at", at))
            result = invoke(*arguments)
    except OSError:
        raise WorkflowError(
            "could not prepare the workflow draft; check file permissions"
        ) from None
    if command == "enqueue":
        if not isinstance(result, dict) or not isinstance(result.get("job_id"), str):
            raise WorkflowError(
                "ai-workflow did not return a job ID; inspect the queue before retrying"
            )
        return {"date": day, "home": str(home()), **result, "approval_required": True}
    return result


def main():
    parser = argparse.ArgumentParser(prog="techbro workflow", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup_command = commands.add_parser(
        "setup", help="configure an explicit account without copying tokens"
    )
    setup_command.add_argument("--provider", choices=("native", "repliz", "mock"), default="native")
    for name in ("preview", "enqueue"):
        child = commands.add_parser(name, help="use the exact requested Techbro draft")
        child.add_argument("--date", default=day_stamp())
        child.add_argument("--key", help="unique release key; default daily-YYYYMMDD")
        child.add_argument("--at", help="ISO datetime with timezone")
    for name in ("status", "events", "cancel", "recover", "retry", "preview-job"):
        commands.add_parser(name).add_argument("job")
    approve = commands.add_parser("approve", help="approve a reviewed release")
    approve.add_argument("job")
    approve.add_argument("--reviewer", required=True)
    commands.add_parser("jobs")
    worker = commands.add_parser("worker", help="process already approved jobs")
    worker.add_argument("--steps", type=int, default=20)
    args = parser.parse_args()
    try:
        if args.command == "setup":
            result = setup(args.provider)
        elif args.command in ("preview", "enqueue"):
            result = draft_operation(args.command, args.date, key=args.key, at=args.at)
        else:
            check_workspace()
            if args.command in ("approve", "worker", "retry"):
                check_publishers()
            if args.command == "approve":
                result = invoke("approve", args.job, "--reviewer", args.reviewer)
            elif args.command == "worker":
                if not 1 <= args.steps <= 100:
                    raise WorkflowError("worker steps must be between 1 and 100")
                result = invoke("worker", "--steps", args.steps)
            elif args.command == "jobs":
                result = invoke("jobs", "--project", "techbro")
            else:
                result = invoke(args.command, args.job)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except WorkflowError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("[error] invalid workflow input or file permissions", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
