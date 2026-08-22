#!/usr/bin/env python3
"""batch_lambdaH_v3.py — 里程碑2 阶段A：上三角打包 kernel 的维度扩展验证
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)

目标：GPU 直跑 d=32/40（v1 全矩阵 local 止于 d=24；d=32 原为 numpy 补充，
d=40 为全新数据点）。打包版 negacyclic_kernel_v3.cl 支持 n=2d ≤ 80。

判据（与 v1 相同）：
  1. CPU numpy 逐位对照（同 PCG32 系数）：max rel|Δλ| < 1e-8
  2. 零方差统计：std(Λ_H) < 1e-12 且 max|Λ_H−1| < 1e-9 → Λ_H ≡ 1（定理 0.9.4.02）
  3. diag 族对照（定理 0.9.4.11）：Λ_H = M² 精确
"""
import argparse
import os
import sys
import time

import numpy as np
import pyopencl as cl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_lambdaH import (get_gpu, batch_lambdaH_gpu, check_cpu_gpu,  # noqa: E402
                           report)

HERE = os.path.dirname(os.path.abspath(__file__))


def build_program_v3(ctx):
    src = open(os.path.join(HERE, "negacyclic_kernel_v3.cl")).read()
    return cl.Program(ctx, src).build()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=32, help="negacyclic 维数（n=2d≤80）")
    ap.add_argument("--N", type=int, default=512, help="样本数")
    ap.add_argument("--q", type=int, default=3329, help="模数")
    ap.add_argument("--check", type=int, default=128, help="CPU 对照样本数")
    args = ap.parse_args()

    d, q, N = args.d, args.q, args.N
    assert 2 * d <= 80, "v3 打包版支持 n=2d ≤ 80（d ≤ 40）"
    assert d % 2 == 0, "定理 0.9.4.02 要求 d 偶（无自共轭根）"

    ctx, queue, dev = get_gpu()
    print(f"[DEVICE] {dev.name}")
    prog = build_program_v3(ctx)

    rng = np.random.default_rng(20260823)
    seeds = rng.integers(0, 2**32, size=N, dtype=np.uint32)

    t0 = time.perf_counter()
    L1, L2, off = batch_lambdaH_gpu(ctx, queue, prog, seeds, d, q)
    dt = time.perf_counter() - t0
    print(f"[GPU v3] d={d} (n={2*d}) N={N}: {dt:.2f}s  ({N/dt/1e3:.1f}k mat/s)")

    err = check_cpu_gpu(seeds, d, q, L1.copy(), L2.copy(), args.check)
    print(f"[对照] CPU numpy vs GPU v3（前 {args.check} 样本）max rel|Δλ| = {err:.3e} "
          f"{'✓' if err < 1e-8 else '✗'}")

    ok = report(f"negacyclic d={d} q={q} (v3 打包)", L1, L2, off)

    # diag 族对照（定理 0.9.4.11：Λ_H = M² 精确，CPU 验证即可）
    for M in (10.0, 100.0):
        G = np.diag([1.0] + [M * M] * (2 * d - 1))
        ev = np.sort(np.linalg.eigvalsh(G))
        Lh = ev[1] / ev[0]
        print(f"[diag 族] M={M:g}: Λ_H = {Lh:.6f}  （定理 0.9.4.11 预言 M²={M*M:.6f}）"
              f" {'✓' if abs(Lh - M * M) < 1e-9 else '✗'}")

    print()
    print("[OK] v3 打包版零方差验证通过" if ok else "[FAIL] 存在波动")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
