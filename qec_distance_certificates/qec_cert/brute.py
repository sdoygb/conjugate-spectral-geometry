"""Brute-force enumeration baseline: streaming enumeration of all flip sets
with syndrome tests.

Counterpart of the certificate path (certificate.py): the same decision
problem (verifying the distance lower bound), where the brute-force path
enumerates the error space sum_{w<d} C(n,w) (exponential in n) while the
certificate path is O(n^2) polynomial.

Measured cross-over (same machine, same implementation, see
geo_qec/bench_out3.txt): brute force wins below ~5e4 enumerations; beyond
that the certificate path dominates with a near-slope-1 curve (speedup
proportional to enumeration size) — for [[1024,252,32]] brute force would
take ~2.4e45 years versus 0.7 seconds for the certificate.

Implementation notes: itertools streaming combination generation +
array('Q') C-level buffering + np.frombuffer zero-copy + vectorized XOR;
measured at ~2.2e6 flip/s (Mac, Python 3.9).
"""
from __future__ import annotations

import itertools
import time
from array import array

import numpy as np

from .rm_codes import build_cols, css_params

__all__ = ["brute_layer", "brute_verify"]


def brute_layer(
    cols: np.ndarray,
    n: int,
    w: int,
    batch: int = 1_000_000,
) -> tuple[int, int, float]:
    """Brute-force enumerate all flip sets of weight w and count
    undetectable (syndrome=0) ones.

    Returns (total enumerated, syndrome=0 count, elapsed seconds).
    syndrome=0 <=> the indicator vector of the flip set is orthogonal to all
    RM basis rows (i.e., lies in the dual code).
    """
    t0 = time.time()
    total = 0
    bad = 0
    it = itertools.combinations(range(n), w)
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            break
        # C-level streaming buffer: bypasses the Python-level
        # tuple-list -> np.array conversion bottleneck
        buf = array("Q", itertools.chain.from_iterable(chunk))
        arr = np.frombuffer(buf, dtype=np.uint64).reshape(len(chunk), w)
        sx = np.bitwise_xor.reduce(cols[arr], axis=1)
        bad += int(np.count_nonzero(sx == 0))
        total += len(chunk)
        del chunk, buf, arr, sx
    return total, bad, time.time() - t0


def brute_verify(
    r: int,
    m: int,
    max_w: int | None = None,
    batch: int = 1_000_000,
    verbose: bool = False,
) -> dict:
    """Brute-force verification of the distance lower bound of CSS(RM(r,m)):
    enumerate all flip sets of weights 1..max_w.

    Returns per-layer statistics
    {w: {"total": ..., "undetected": ..., "elapsed": ...}}.
    max_w=None means d-1 (full lower-bound verification).
    """
    n, k, d = css_params(r, m)
    if max_w is None:
        max_w = d - 1
    cols, _ = build_cols(r, m)
    layers: dict[int, dict] = {}
    t_all = time.time()
    for w in range(1, max_w + 1):
        total, bad, dt = brute_layer(cols, n, w, batch=batch)
        layers[w] = {"total": total, "undetected": bad, "elapsed": dt}
        if verbose:
            rate = total / dt if dt > 0 else float("inf")
            print(f"[brute] w={w}: {total:,} flips, undetected={bad}, "
                  f"{dt:.2f}s ({rate:,.0f} flip/s)")
    layers["_summary"] = {
        "n": n,
        "k": k,
        "d": d,
        "total_flips": sum(v["total"] for w, v in layers.items() if isinstance(w, int)),
        "total_undetected": sum(v["undetected"] for w, v in layers.items() if isinstance(w, int)),
        "elapsed": time.time() - t_all,
    }
    return layers
