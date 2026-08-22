#!/usr/bin/env python3
"""d48_numpy_check.py — d=48（n=96）维度独立性验证（GPU local 内存受限，numpy 补充）

背景：negacyclic_kernel.cl NMAX=48（Apple AMD 编译器 32KB local 数组限制，
96×96×8=73.7KB 超限）。d=48 需 n=96 Gram 矩阵，GPU 编不过 → 用 numpy eigvalsh
（与报告 d=32 numpy 补充同法），验证定理 0.9.4.02 在 d=48 仍成立：λ1=λ2，Λ_H≡1。

判据：std 应达 double 机器精度级（简并特征值数值分裂，~1e-12 量级）。
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_lambdaH import gen_coefs_cpu, build_G_cpu  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=48, help="negacyclic 维数（n=2d）")
    ap.add_argument("--N", type=int, default=512, help="样本数")
    ap.add_argument("--q", type=int, default=3329, help="模数")
    args = ap.parse_args()
    d, q, N = args.d, args.q, args.N
    assert d % 2 == 0, "定理 0.9.4.02 要求 d 偶"

    rng = np.random.default_rng(20260823)
    seeds = rng.integers(0, 2**32, size=N, dtype=np.uint32)

    t0 = time.perf_counter()
    L1 = np.empty(N)
    L2 = np.empty(N)
    for i, s in enumerate(seeds):
        coefs = gen_coefs_cpu(int(s), d, q)
        G = build_G_cpu(coefs, d, q)
        ev = np.sort(np.linalg.eigvalsh(G))
        L1[i], L2[i] = ev[0], ev[1]
    dt = time.perf_counter() - t0

    LambdaH = L2 / L1
    mu = float(LambdaH.mean())
    sd = float(LambdaH.std())
    mx = float(np.max(np.abs(LambdaH - 1.0)))
    mn, mm = float(LambdaH.min()), float(LambdaH.max())
    print(f"[CPU numpy] d={d} (n={2*d}) N={N}: {dt:.1f}s  ({N/dt:.1f} mat/s)")
    print(f"[negacyclic d={d} q={q}] Λ_H: mean={mu:.12f}  std={sd:.3e}  "
          f"min={mn:.12f}  max={mm:.12f}  max|Λ_H-1|={mx:.3e}")
    print(f"          λ1: mean={L1.mean():.4f}  min={L1.min():.4f}  max={L1.max():.4f}")
    zero_var = sd < 1e-11 and mx < 1e-9
    print(f"          零方差判定: {'✓ 确认 Λ_H ≡ 1' if zero_var else '✗ 存在波动'}")

    # diag 族对照（定理 0.9.4.11，n=96 规模）
    for M in (10.0, 100.0):
        G = np.diag([1.0] + [M * M] * (2 * d - 1))
        ev = np.sort(np.linalg.eigvalsh(G))
        Lh = ev[1] / ev[0]
        print(f"[diag 族 n={2*d}] M={M:g}: Λ_H = {Lh:.6f}  "
              f"（定理 0.9.4.11 预言 M²={M*M:.6f}） {'✓' if abs(Lh - M*M) < 1e-9 else '✗'}")
    return 0 if zero_var else 1


if __name__ == "__main__":
    raise SystemExit(main())
