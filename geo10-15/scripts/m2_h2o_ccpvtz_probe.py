#!/usr/bin/env python3
"""M2 probe: H2O/cc-pVTZ (n_orb=58, dim=2.1e13) — build cost, HF ball size,
row degree, GPU occupancy-aware doubles availability.  No heavy solve.

Usage:  PYTHONPATH=. .venv311/bin/python3 -u geo10-15/scripts/m2_h2o_ccpvtz_probe.py
"""
import sys, os, time
import numpy as np
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEOQC = os.path.join(os.path.dirname(ROOT), "geocore")
for p in (ROOT, GEOQC):
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    t_start = time.time()
    d = np.load(os.path.join(GEOQC, "data", "h2o_ccpvtz_integrals.npz"))
    n_orb = int(d["n"]); n_occ = 5
    h_sp = d["h"]; t_sp = d["t"]; nuc = float(d["nuc"])
    e_ccsdt = float(d["e_ccsdt"])
    da = comb(n_orb, n_occ); db = comb(n_orb, n_occ)
    dim = da * db
    print(f"H2O/cc-pVTZ: n_orb={n_orb}, n_occ={n_occ}, dim={dim:.3e}")
    print(f"CCSD(T)={e_ccsdt:.10f}  (target: < 1.59 mHa of this)")
    row_deg = (2 * n_occ * (n_orb - n_occ)
               + 2 * comb(n_occ, 2) * comb(n_orb - n_occ, 2)
               + (n_occ * (n_orb - n_occ)) ** 2)
    print(f"combinatorial row degree ~= {row_deg:,}  "
          f"(incl. two-body diag in row==col)")

    # rank tables cost (combinatorial, no O(2^n))
    t0 = time.time()
    from solver.system import SectorSystem
    print("\nBuilding SectorSystem (CPU t_s would be "
          f"{2*n_orb}**4 * 16 B = {(2*n_orb)**4*16/1e9:.1f} GB — checking "
          f"GPU path instead)...", flush=True)

    # GPU occupancy-aware doubles (spatial tensor, skips t_s)
    gpu_apply = None
    try:
        sys.path.insert(0, GEOQC + "/examples")
        from gpu_occ_aware_doubles_sp import GPUApplyOccAwareSP
        from geoqc.gpu import _get_global_gpu
        gpu_ctx, gpu_queue, _ = _get_global_gpu()
        gpu_apply = GPUApplyOccAwareSP(n_orb, n_occ, t_sp, eps=1e-4,
                                       chunk_size=32)
        print(f"GPUApplyOccAwareSP ready (skips t_s; spatial "
              f"{t_sp.nbytes/1e6:.0f} MB)")
    except Exception as e:
        print(f"GPU unavailable ({type(e).__name__}: {e}) -> will need t_s")

    # build system with the GPU apply (t_s skipped); rank tables C(58,5)
    sys0 = SectorSystem(n_orb, n_occ, n_occ, h_sp, t_sp, nuc, eps=1e-4,
                        gpu_apply=gpu_apply)
    print(f"SectorSystem built in {time.time()-t_start:.1f}s; "
          f"seed_idx={sys0.seed_idx}")

    # HF Bruhat ball size + row degree (measured)
    t0 = time.time()
    ball, _ = sys0.h_col(sys0.seed_idx)
    print(f"HF Bruhat 2-ball: {len(ball)} states "
          f"(built {time.time()-t0:.1f}s)")
    # row degree on one random out-state via apply on 1 state
    t0 = time.time()
    u, w = sys0.apply_H_on(np.array([sys0.seed_idx], dtype=np.int64),
                           np.ones(1))
    print(f"apply on 1 state: {len(u)} targets in {time.time()-t0:.2f}s")
    print(f"\nprobe total {time.time()-t_start:.1f}s")
    print("OK")


if __name__ == "__main__":
    main()
