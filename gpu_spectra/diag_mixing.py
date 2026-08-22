#!/usr/bin/env python3
"""diag_mixing.py — 系综混合度诊断：nsteps 对 Λ_H 系综统计的影响
问题：highsym_spectra.ensemble 用固定 nsteps=40，对 d=24 混合不足（U 接近单位阵）。
诊断：对 Leech / Z^24 / 随机24，扫描 nsteps ∈ {40,100,200,400}，对比 std_raw 与 LLL 后 std。
"""
import sys
sys.path.insert(0, "gpu_spectra")
import numpy as np
from highsym_spectra import (leech_basis, z_basis, random_basis,
                             random_unimodular, lll_reduce, lambda_H)

def diag(B, name, nsteps_list, N=100, seed=20260823):
    rng = np.random.default_rng(seed)
    d = B.shape[0]
    print(f"\n=== {name} (d={d}) N={N} ===")
    print(f"{'nsteps':>8s}{'std_raw':>12s}{'mean_LLL':>12s}{'std_LLL':>12s}{'max|Λ_H−1|':>14s}")
    for ns in nsteps_list:
        lam_raw = np.empty(N)
        lam_lll = np.empty(N)
        for t in range(N):
            U = random_unimodular(d, ns, rng)
            BU = B @ U
            lam_raw[t] = lambda_H(BU)
            lam_lll[t] = lambda_H(lll_reduce(BU))
        print(f"{ns:>8d}{lam_raw.std():>12.3e}{lam_lll.mean():>12.6f}"
              f"{lam_lll.std():>12.3e}{np.max(np.abs(lam_lll-1)):>14.3e}")

if __name__ == "__main__":
    print("Leech 构造:", end=" ")
    try:
        Bleech = leech_basis()
        print("OK")
    except Exception as e:
        print(f"FAIL {e}")
        sys.exit(1)
    diag(Bleech, "Leech Λ24", [40, 100, 200, 400])
    diag(z_basis(24), "Z^24", [40, 100, 200, 400])
    diag(random_basis(24), "随机24", [40, 100, 200, 400])
