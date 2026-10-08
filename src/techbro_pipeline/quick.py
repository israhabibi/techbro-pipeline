"""Short Indonesian commands for reviewing and dispatching the shared outbox."""

import argparse
import getpass
import sys

from techbro_pipeline import workflow
from techbro_pipeline.config import day_stamp


def show_preview(preview):
    account = preview["account"]
    print(f"Tujuan: {account['name']} ({account['provider']})")
    if "job" in preview:
        print(f"Job: {preview['job']['id']} | {preview['job']['state']}")
    post = preview["post"]
    parts = [post["text"], *post.get("replies", [])]
    for index, text in enumerate(parts, 1):
        print(f"\nBagian {index}/{len(parts)}\n{text}")


def main(command, arguments):
    parser = argparse.ArgumentParser(prog=f"techbro {command}")
    if command == "lihat":
        parser.add_argument(
            "target", nargs="?", help="JOB_ID or YYYYMMDD; defaults to today's draft"
        )
    elif command == "setujui":
        parser.add_argument("job")
        parser.add_argument("--reviewer", default=getpass.getuser())
    options = parser.parse_args(arguments)
    try:
        workflow.check_workspace()
        if command == "lihat":
            target = options.target or day_stamp()
            if len(target) == 8 and target.isdigit():
                preview = workflow.draft_operation("preview", target)
            else:
                preview = workflow.invoke("preview-job", target)
            show_preview(preview)
        elif command == "antrean":
            jobs = workflow.invoke("jobs", "--project", "techbro")
            if not jobs:
                print("Antrean kosong.")
            for job in jobs:
                print(f"{job['state']} | {job['release_key']} | {job['id']}")
        elif command == "setujui":
            workflow.check_publishers()
            job = workflow.invoke("approve", options.job, "--reviewer", options.reviewer)
            print(f"Disetujui: {job['id']}. Jalankan techbro kirim untuk memprosesnya.")
        elif command == "kirim":
            workflow.check_publishers()
            outcomes = workflow.invoke("worker", "--steps", 20)
            if not outcomes:
                print("Tidak ada posting yang siap dikirim saat ini.")
            latest = {job["id"]: job for job in outcomes}
            for job in latest.values():
                print(f"{job['state']} | {job['id']}")
            if any(job["state"] == "queued" for job in latest.values()):
                print(
                    "Masih menunggu pemrosesan. Jalankan techbro kirim lagi setelah beberapa detik."
                )
            if any(job["state"] in {"failed", "needs_review"} for job in latest.values()):
                print("Periksa status dan hasil di platform sebelum mencoba lagi.")
                return 1
        return 0
    except workflow.WorkflowError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit("Use techbro lihat, antrean, setujui or kirim")
