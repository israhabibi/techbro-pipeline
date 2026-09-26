#!/usr/bin/env python3
"""CPU/intrusion watchdog for the techbro VPS.
Runs every 5 min via Hermes cron (no_agent). Sends a Telegram alert ONLY when
something looks wrong (high load, or SSH auth failures). Exits silent otherwise.

Alerts on:
  - 1-min load avg > 0.80 * nproc  (≈ CPU saturated on this 2-vCPU box)
  - sshd journal shows >= 5 auth failures in the last 5 min
Sends via Hermes telegram delivery by printing a message to stdout.
"""
import os, sys, subprocess, json

# --- thresholds ---
LOAD_RATIO = 0.80          # fraction of total CPU capacity considered "high"
FAIL_THRESHOLD = 5         # ssh auth failures in window to alert

def nproc():
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1

def load1():
    try:
        return float(open("/proc/loadavg").read().split()[0])
    except Exception:
        return 0.0

def ssh_fails_last_minutes(mins=5):
    try:
        out = subprocess.run(
            ["journalctl", "-u", "sshd", f"--since={mins} min ago", "-o", "cat", "-q"],
            capture_output=True, text=True, timeout=20).stdout
        # count lines that look like failures
        bad = sum(1 for l in out.splitlines()
                  if any(k in l for k in ("Failed password", "invalid user",
                                          "authentication failure", "Connection closed")))
        return bad
    except Exception:
        return 0

def main():
    n = nproc()
    l1 = load1()
    high_load = l1 > LOAD_RATIO * n
    fails = ssh_fails_last_minutes(5)

    alerts = []
    if high_load:
        alerts.append(f"🔥 CPU load tinggi: {l1:.2f} (batas {LOAD_RATIO*n:.2f}) di VPS 2-CPU")
    if fails >= FAIL_THRESHOLD:
        alerts.append(f"⚠️ SSH gagal login {fails}x dalam 5 menit terakhir (curiga bruteforce?)")

    if not alerts:
        # silent — nothing to report
        sys.exit(0)

    msg = "🤖 *VPS Watchdog Alert*\n" + "\n".join(f"• {a}" for a in alerts) + \
          f"\n\nLoad: {l1:.2f} | CPU: {n} core | SSH-fail(5m): {fails}"
    print(msg)

if __name__ == "__main__":
    main()
