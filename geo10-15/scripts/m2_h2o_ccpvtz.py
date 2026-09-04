#!/usr/bin/env python3
"""M2: H2O/cc-pVTZ (n_orb=58, dim=2.1e13) — descent to chemical accuracy.

Scale-up from M1: no dense anchor (dim 2.1e13); CCSD(T) reference
-76.3457672654 Ha.  Uses GPU occupancy-aware doubles (skips t_s) and
truncated Bruhat balls (max_wp_size) for memory safety on 16 GB.

Target: |E_var + E_corr - CCSD(T)| < 1.59 mHa.

Usage:  PYTHONPATH=. .venv311/bin/python3 -u geo10-15/scripts/m2_h2o_ccpvtz.py
"""
import sys, os, time, gc
import numpy as np
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEOQC = os.path.join(os.path.dirname(ROOT), "geocore")
for p in (ROOT, GEOQC):
    if p not in sys.path:
        sys.path.insert(0, p)

from solver.system import SectorSystem
from solver.descent import Descent
from solver import verify


def main():
    print("=" * 78)
    print("M2  H2O/cc-pVTZ  constrained-submanifold Newton descent "
          "(dim 2.1e13)")
    print("=" * 78)
    t_start = time.time()

    d = np.load(os.path.join(GEOQC, "data", "h2o_ccpvtz_integrals.npz"))
    n_orb = int(d["n"]); n_occ = 5
    h_sp = d["h"]; t_sp = d["t"]; nuc = float(d["nuc"])
    e_ccsdt = float(d["e_ccsdt"])
    dim = comb(n_orb, n_occ) ** 2
    print(f"n_orb={n_orb}, n_occ={n_occ}, dim={dim:.3e}")
    print(f"CCSD(T)={e_ccsdt:.10f} Ha  (target < 1.59 mHa)")

    # GPU occupancy-aware doubles (spatial tensor; skip 2.9 GB t_s)
    gpu_apply = None
    sys.path.insert(0, GEOQC + "/examples")
    from gpu_occ_aware_doubles_sp import GPUApplyOccAwareSP
    from geoqc.gpu import _get_global_gpu
    gpu_ctx, gpu_queue, _ = _get_global_gpu()
    gpu_apply = GPUApplyOccAwareSP(n_orb, n_occ, t_sp, eps=1e-4,
                                   chunk_size=32)
    print(f"GPUApplyOccAwareSP ready ({t_sp.nbytes/1e6:.0f} MB spatial)")

    print("\nBuilding SectorSystem ...", flush=True)
    t0 = time.time()
    sys0 = SectorSystem(n_orb, n_occ, n_occ, h_sp, t_sp, nuc, eps=1e-4,
                        gpu_apply=gpu_apply)
    print(f"built in {time.time()-t0:.1f}s; seed_idx={sys0.seed_idx}")

    # HF Bruhat ball size (measured in probe: 25720)
    t0 = time.time()
    ball0, _ = sys0.h_col(sys0.seed_idx)
    print(f"HF Bruhat ball: {len(ball0)} states "
          f"({time.time()-t0:.1f}s)", flush=True)

    # ---- descent: truncated balls for memory safety ----
    print("\n--- descent (correct-then-expand, dual stop 9.2) ---", flush=True)
    d = Descent(sys0, chem_tol=1.59e-3, max_wavepackets=30,
                n_centers=20, max_block=6000, h_chunk=64,
                jacobi_sweeps=0, ball_cover_topk=100, verbose=True,
                max_wp_size=6000)
    t0 = time.time()
    E_final, E_var, E_corr, V_fin, c_fin, stats = d.run()
    wall = time.time() - t0
    print(f"\ndescent wall = {wall:.1f}s = {wall/60:.1f} min; "
          f"|V_final|={len(V_fin)}", flush=True)

    # machine-precision checks
    ok_sign = verify.check_sign(stats, raise_on_error=False)
    ok_mono = verify.check_monotone(stats, raise_on_error=False)
    print(f"sign check (E_corr<=0): {ok_sign}")
    print(f"monotonicity (E_var non-increasing): {ok_mono}")

    err = (E_final - e_ccsdt) * 1000
    print(f"\nCCSD(T) = {e_ccsdt:+.10f} Ha")
    print(f"E_final (E_var+E_corr) = {E_final:+.10f} Ha")
    print(f"final error vs CCSD(T) = {err:+.4f} mHa  "
          f"(chemical accuracy 1.59 mHa)  {'PASS' if abs(err) < 1.59 else 'FAIL'}")
    print(f"total wall = {(time.time()-t_start)/60:.2f} min")
    print("=" * 78)


if __name__ == "__main__":
    main()
