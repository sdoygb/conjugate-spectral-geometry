"""RunMonitor: markers / status probe / heartbeat / stall detection for
long background geo10-15 jobs.  Builds the observability layer agreed with
the user (2026-09-03):

  ① markers  — every phase logs entry with timestamp + progress + RSS
  ② probe    — a live <run>.status JSON file, updated on heartbeat:
                phase, phase_started, last_heartbeat, rss, cpu, progress
  ③ feedback — stall detection helpers the external watchdog calls:
                CPU low + phase not advancing + over-budget -> kill+dump
  ④ checkpoint — per-phase save/resume of heavy intermediates (V, H,
                H_cols, round energies) so a killed job resumes, not reruns

Usage pattern (in a long-running script):

    mon = RunMonitor("m2_fullball", notes_dir=..., budget={
               "H_build": (400, 900),      # (expected_s, max_s)
               "eigh":    (60, 300),
           })
    mon.phase("H_build", n_total=60)
    for chunk in range(60):
        ... do chunk ...
        mon.progress(chunk + 1)   # heartbeat with progress
    H = ...
    mon.phase("eigh")
    ev = ...
    mon.done(result={"E_var": ev})

The external watchdog (scripts/_watch.py) reads <run>.status and enforces
the stall policy (auto kill + dump).  The job itself never waits silently.
"""
import os
import json
import time
import traceback


def _rss_mb():
    """Current RSS in MB (portable; macOS ru_maxrss is bytes)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
    except Exception:
        return -1.0


class RunMonitor:
    def __init__(self, name, notes_dir, budget=None, log=None):
        self.name = name
        self.notes_dir = notes_dir
        os.makedirs(notes_dir, exist_ok=True)
        self.status_path = os.path.join(notes_dir, f"{name}.status")
        self.log_path = log or os.path.join(notes_dir, f"{name}.run.log")
        self.budget = budget or {}   # phase -> (expected_s, max_s)
        self.t0 = time.time()
        self.phase_name = None
        self.phase_t0 = None
        self.phase_meta = {}
        self.last_heartbeat = time.time()
        self.n_total = None
        self.n_done = 0
        self._write_status(state="starting")

    # ------------------------------------------------------------- plumbing
    def _write_status(self, **extra):
        st = {
            "name": self.name,
            "state": extra.get("state", "running"),
            "phase": self.phase_name,
            "phase_elapsed_s": (round(time.time() - self.phase_t0, 1)
                                if self.phase_t0 is not None else 0.0),
            "total_elapsed_s": round(time.time() - self.t0, 1),
            "last_heartbeat": time.time(),
            "rss_mb": round(_rss_mb(), 1),
            "progress": (f"{self.n_done}/{self.n_total}"
                         if self.n_total else None),
            "pid": os.getpid(),
        }
        st.update(extra)
        with open(self.status_path, "w") as f:
            json.dump(st, f)
        self.last_heartbeat = time.time()

    def _log(self, msg):
        line = (f"[T+{time.time() - self.t0:7.1f}s] "
                f"[{self.phase_name or '-'}] {msg}")
        print(line, flush=True)
        try:
            with open(self.log_path, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass

    # ------------------------------------------------------------- markers
    def phase(self, name, n_total=None, note=None):
        """Enter a new phase: log entry with timestamp, RSS, budget window."""
        self.phase_name = name
        self.phase_t0 = time.time()
        self.n_total = n_total
        self.n_done = 0
        exp, mx = self.budget.get(name, (None, None))
        budget_str = ""
        if exp or mx:
            budget_str = (f"  [budget: expected<={exp or '?'}s"
                          f" max<={mx or '?'}s]")
        self._log(f"ENTER phase={name} RSS={_rss_mb():.0f}MB"
                  f"{budget_str}{'  note: ' + note if note else ''}")
        self._write_status(state="running")

    def progress(self, done, note=None):
        """Heartbeat with progress; called every chunk."""
        self.n_done = int(done)
        self._write_status(state="running")
        if note:
            self._log(f"progress {done}/{self.n_total} {note}")
        # cheap throttle: only log every ~2% of a large phase
        return True

    def heartbeat(self, note=None):
        self._write_status(state="running")
        if note:
            self._log(note)

    # ------------------------------------------------------------ feedback
    def stall_check(self):
        """In-process cheap stall probe: over-budget phase -> warn (the
        external watchdog decides).  Returns True if over max budget."""
        if self.phase_name is None or self.phase_t0 is None:
            return False
        exp, mx = self.budget.get(self.phase_name, (None, None))
        if mx is None:
            return False
        el = time.time() - self.phase_t0
        return el > mx

    def dump(self, reason, exc=None):
        """Write a diagnostic dump (phase, timing, RSS, traceback)."""
        self._log(f"DUMP requested: {reason}")
        if exc is not None:
            self._log("".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__)))
        self._write_status(state="dumped", dump_reason=reason)

    def done(self, result=None):
        self._log(f"DONE total={time.time() - self.t0:.1f}s "
                  f"RSS={_rss_mb():.0f}MB")
        self._write_status(state="done", result=result)
        return result


# ---------------------------------------------------------------------------
# Checkpoint: per-phase save/resume of heavy intermediates
# ---------------------------------------------------------------------------

def save_checkpoint(notes_dir, name, tag, payload):
    """Persist {key: np.ndarray | float | dict-of-arrays} to an npz file.
    Convention: <notes_dir>/<name>.ckpt-<tag>.npz (arrays stored by key;
    scalars wrapped).  Returns the path."""
    import numpy as np
    path = os.path.join(notes_dir, f"{name}.ckpt-{tag}.npz")
    save = {}
    for k, v in payload.items():
        if isinstance(v, dict):
            # dict of arrays (e.g. H_cols): store flattened keys
            for kk, vv in v.items():
                save[f"{k}::{kk}"] = np.asarray(vv)
        else:
            save[k] = np.asarray(v)
    np.savez_compressed(path, **save)
    return path


def load_checkpoint(notes_dir, name, tag):
    """Load an npz checkpoint back into the same shape {key: array |
    {subkey: array}} (keys containing '::' are reassembled into dicts)."""
    import numpy as np
    path = os.path.join(notes_dir, f"{name}.ckpt-{tag}.npz")
    if not os.path.exists(path):
        return None
    with np.load(path, allow_pickle=False) as d:
        plain, nested = {}, {}
        for k in d.files:
            if "::" in k:
                head, _, tail = k.partition("::")
                nested.setdefault(head, {})[tail] = d[k]
            else:
                plain[k] = d[k]
    plain.update(nested)
    return plain
