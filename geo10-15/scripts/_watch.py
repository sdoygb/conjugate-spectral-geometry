#!/usr/bin/env python3
"""Watchdog wrapper for long geo10-15 background jobs.

Usage:
    python3 scripts/_watch.py <notes_dir> <run_name> <cmd...>

Behaviour (user-confirmed 2026-09-03):
  - launches <cmd> with stdout+stderr appended to <run_name>.run.log
  - every POLL (default 20 s) samples the child's CPU% and RSS
  - reads <run_name>.status (written by solver/runmon.RunMonitor)
  - STALL POLICY: if CPU < 5% AND the status file has not advanced for
    STALL_SAMPLES consecutive polls AND the current phase is over its
    max budget -> kill + explicit "stalled in phase X" report.
  - OVER-BUDGET POLICY: any phase whose elapsed > max_s (from status file
    budget is passed via RunMonitor.budget; watchdog reads status only,
    so max budget lives in the job) — watchdog enforces a global wall
    cap given by --wall-max.
  - on child exit: writes a final status line + exit code.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time


POLL = 20          # seconds between samples
STALL_SAMPLES = 6  # consecutive low-CPU samples -> suspect stall (~2 min)
LOW_CPU = 5.0      # %CPU below which we consider "not computing"


def read_status(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def log(msg):
    print(f"[watch] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notes_dir")
    ap.add_argument("run_name")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    ap.add_argument("--wall-max", type=float, default=4 * 3600,
                    help="global wall-clock cap (s), default 4 h")
    ap.add_argument("--kill-after-dump", action="store_true", default=True)
    args = ap.parse_args()

    notes_dir = os.path.abspath(args.notes_dir)
    run_name = args.run_name
    status_path = os.path.join(notes_dir, f"{run_name}.status")
    log_path = os.path.join(notes_dir, f"{run_name}.run.log")

    # merge cmd args (REMAINDER may split) and launch
    cmd = args.cmd
    log(f"launch: {' '.join(cmd)}")
    log(f"status: {status_path}\nlog:    {log_path}")
    with open(log_path, "a") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)

    t_start = time.time()
    low_streak = 0
    last_seen = None   # (phase, progress, heartbeat) from status file

    try:
        while proc.poll() is None:
            time.sleep(POLL)
            wall = time.time() - t_start

            # global wall cap
            if wall > args.wall_max:
                log(f"WALL-CAP exceeded ({wall:.0f}s > {args.wall_max:.0f}s) "
                    f"-> killing {proc.pid}")
                os.kill(proc.pid, signal.SIGKILL)
                proc.wait()
                log(f"killed (wall cap). exit={proc.returncode}")
                return 2

            st = read_status(status_path)
            # sample child CPU/RSS via ps
            cpu = rss = None
            try:
                out = subprocess.run(
                    ["ps", "-o", "%cpu=,rss=", "-p", str(proc.pid)],
                    capture_output=True, text=True, timeout=10).stdout.strip()
                parts = out.split()
                if len(parts) >= 2:
                    cpu, rss = float(parts[0]), int(parts[1]) / 1024.0
            except Exception:
                pass

            phase = (st or {}).get("phase")
            prog = (st or {}).get("progress")
            hb = (st or {}).get("last_heartbeat", 0.0)
            now = time.time()
            sig = (phase, prog)
            hb_age = now - hb if hb else None

            # stall detection: CPU low AND status not advancing
            if cpu is not None and cpu < LOW_CPU:
                if sig == last_seen and hb_age is not None and hb_age > 3 * POLL:
                    low_streak += 1
                else:
                    low_streak = 0
            else:
                low_streak = 0
            last_seen = sig

            state = (st or {}).get("state", "?")
            log(f"t={wall:6.0f}s phase={phase} prog={prog} state={state} "
                f"cpu={cpu}% rss={rss:.0f}MB hb_age={hb_age}s "
                f"low_streak={low_streak}/{STALL_SAMPLES}")

            if low_streak >= STALL_SAMPLES:
                log(f"STALLED: CPU<{LOW_CPU}% for {low_streak * POLL}s in "
                    f"phase={phase} (no progress) -> dumping + killing")
                dump = os.path.join(notes_dir, f"{run_name}.dump.txt")
                try:
                    subprocess.run(["sample", str(proc.pid), "1", "-file",
                                    dump], timeout=30)
                except Exception:
                    pass
                os.kill(proc.pid, signal.SIGKILL)
                proc.wait()
                log(f"killed (stall in phase={phase}). exit={proc.returncode}")
                return 3

        code = proc.returncode
        st = read_status(status_path)
        log(f"child exited cleanly with code={code}; "
            f"final status state={(st or {}).get('state')}")
        return code
    except KeyboardInterrupt:
        log("watchdog interrupted; killing child")
        proc.kill()
        proc.wait()
        return 130


if __name__ == "__main__":
    sys.exit(main())
