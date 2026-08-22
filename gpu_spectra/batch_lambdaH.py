#!/usr/bin/env python3
"""batch_lambdaH.py — 零方差定律大规模验证（0.9 §4.3 定理 0.9.4.02/0.9.4.10）
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
里程碑 1：negacyclic 无调制格 Λ_H ≡ 1 的 N=10^5 级确认（0.9 目前仅 N=20）

流程：
  1. CPU 生成 N 个种子（numpy，可复现）
  2. GPU 批量：PCG32 系数 → 组装 G = [[AA^T+I, qI], [qI, q^2I]] → Jacobi → (λ1, λ2)
  3. 对照：前 CHECK 个种子用 CPU（同 PCG32 系数 + numpy eigvalsh）逐位核对
  4. 统计：Λ_H = λ2/λ1 的 mean/std/max|Λ_H-1| → 零方差判定

理论断言（0.9 定理 0.9.4.02）：negacyclic 无调制格 λ1(G) = λ2(G)，Λ_H ≡ 1（确定性）。
"""
import argparse
import os
import time

import numpy as np
import pyopencl as cl

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------- PCG32（Python 版，与 kernel 逐位一致） ----------------

def pcg32_stream(seed):
    """生成 PCG32 随机数流（32 位无符号，与 OpenCL uint 回绕一致）
    时序：先取旧 state 生成 word，再更新 state——与 negacyclic_kernel.cl 的
    pcg32() 指针语义逐位一致（GPU 用旧值；旧版误用新值导致序列整体错位）"""
    state = np.uint32(seed)
    while True:
        old = state
        state = np.uint32(old * np.uint32(747796405) + np.uint32(2891336453))
        word = np.uint32(
            ((old >> (np.uint32((old >> np.uint32(28)) + np.uint32(4)))) ^ old)
            * np.uint32(277803737))
        yield np.uint32((word >> np.uint32(22)) ^ word)


def gen_coefs_cpu(seed, d, q):
    """同 kernel：顺序生成 d 个系数，对称盒 [-q/2, q/2]"""
    gen = pcg32_stream(seed)
    half = q // 2
    coefs = np.empty(d, np.float64)
    for k in range(d):
        r = next(gen)
        coefs[k] = float(np.uint32(r % np.uint32(q))) - half
    return coefs


def build_G_cpu(coefs, d, q):
    """G = [[AA^T + I, qI], [qI, q^2 I]]（2d×2d，numpy 参考实现）"""
    a = coefs
    # negacyclic A[i][k] = a[(k-i) mod d] * (k>=i ? +1 : -1)
    idx = np.arange(d)[:, None]          # i
    kdx = np.arange(d)[None, :]          # k
    t = kdx - idx
    sgn = np.where(t >= 0, 1.0, -1.0)
    A = sgn * a[(t % d)]
    G11 = A @ A.T + np.eye(d)
    G12 = np.eye(d) * q
    G22 = np.eye(d) * (q * q)
    G = np.block([[G11, G12], [G12, G22]])
    return G


# ---------------- GPU ----------------

def get_gpu():
    platform = cl.get_platforms()[0]
    devices = platform.get_devices()
    gpu = [dd for dd in devices if dd.type == cl.device_type.GPU]
    dev = gpu[0] if gpu else devices[0]
    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx)
    return ctx, queue, dev


def build_program(ctx):
    src = open(os.path.join(HERE, "negacyclic_kernel.cl")).read()
    return cl.Program(ctx, src).build()


def batch_lambdaH_gpu(ctx, queue, prog, seeds, d, q, wg=None):
    """GPU 批量：返回 (L1, L2, offdiag) 各 [N]"""
    N = len(seeds)
    n = 2 * d
    if wg is None:
        wg = min(2 * n, 256)
    mf = cl.mem_flags
    seeds_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                          hostbuf=np.ascontiguousarray(seeds, np.uint32))
    L1_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    L2_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    off_buf = cl.Buffer(ctx, mf.WRITE_ONLY, N * 8)
    prog.batch_lambdaH(queue, (N * wg,), (wg,),
                       seeds_buf, np.int32(d), np.int32(q),
                       L1_buf, L2_buf, off_buf)
    L1 = np.empty(N, np.float64)
    L2 = np.empty(N, np.float64)
    off = np.empty(N, np.float64)
    cl.enqueue_copy(queue, L1, L1_buf)
    cl.enqueue_copy(queue, L2, L2_buf)
    cl.enqueue_copy(queue, off, off_buf)
    queue.finish()
    return L1, L2, off


# ---------------- 对照与统计 ----------------

def check_cpu_gpu(seeds, d, q, L1, L2, check=128):
    """前 check 个种子：CPU numpy 参考 vs GPU，逐位同 PCG32 系数
    判据：相对特征值误差。绝对误差随谱尺度（λ~1e4–1e7）放大，绝对判据无意义；
    特征值问题标准误差界 = eps×cond，rel 阈值 1e-8 已远超实测 1e-11"""
    rels = []
    for s in seeds[:check]:
        coefs = gen_coefs_cpu(int(s), d, q)
        G = build_G_cpu(coefs, d, q)
        ev = np.sort(np.linalg.eigvalsh(G))
        l1c, l2c = ev[0], ev[1]
        r = max(abs(l1c - L1[0]) / l1c, abs(l2c - L2[0]) / l2c)
        rels.append(r)
        L1 = L1[1:]
        L2 = L2[1:]
    return float(max(rels))


def report(name, L1, L2, off):
    LambdaH = L2 / L1
    mu = float(LambdaH.mean())
    sd = float(LambdaH.std())
    mx = float(np.max(np.abs(LambdaH - 1.0)))
    mn, mm = float(LambdaH.min()), float(LambdaH.max())
    bad_conv = int(np.sum(off > 1e-12))
    print(f"[{name}] N={len(LambdaH)}  Λ_H: mean={mu:.12f}  std={sd:.3e}  "
          f"min={mn:.12f}  max={mm:.12f}  max|Λ_H-1|={mx:.3e}")
    print(f"          λ1: mean={L1.mean():.6f}  min={L1.min():.6f}  max={L1.max():.6f}")
    print(f"          offdiag²>1e-12 的格数: {bad_conv}  "
          f"<offdiag²>={off.mean():.3e}")
    zero_var = sd < 1e-12 and mx < 1e-9
    print(f"          零方差判定: {'✓ 确认 Λ_H ≡ 1' if zero_var else '✗ 存在波动'}")
    return zero_var


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=16, help="negacyclic 维数（n=2d≤64）")
    ap.add_argument("--N", type=int, default=100000, help="样本数")
    ap.add_argument("--q", type=int, default=3329, help="模数")
    ap.add_argument("--check", type=int, default=128, help="CPU 对照样本数")
    args = ap.parse_args()

    d, q, N = args.d, args.q, args.N
    assert 2 * d <= 48, "n=2d 需 ≤ 48（Apple AMD 编译器限制）"
    assert d % 2 == 0, "定理 0.9.4.02 要求 d 偶（无自共轭根）"

    ctx, queue, dev = get_gpu()
    print(f"[DEVICE] {dev.name}")
    prog = build_program(ctx)

    rng = np.random.default_rng(20260822)
    seeds = rng.integers(0, 2**32, size=N, dtype=np.uint32)

    t0 = time.perf_counter()
    L1, L2, off = batch_lambdaH_gpu(ctx, queue, prog, seeds, d, q)
    dt = time.perf_counter() - t0
    print(f"[GPU] d={d} (n={2*d}) N={N}: {dt:.2f}s  ({N/dt/1e3:.1f}k mat/s)")

    err = check_cpu_gpu(seeds, d, q, L1.copy(), L2.copy(), args.check)
    print(f"[对照] CPU numpy vs GPU（前 {args.check} 样本）max rel|Δλ| = {err:.3e} "
          f"{'✓' if err < 1e-8 else '✗'}")

    ok = report(f"negacyclic d={d} q={q}", L1, L2, off)

    # diag 族对照（定理 0.9.4.11：Λ_H = M² 精确，CPU 验证即可）
    for M in (10.0, 100.0):
        G = np.diag([1.0] + [M * M] * (2 * d - 1))
        ev = np.sort(np.linalg.eigvalsh(G))
        Lh = ev[1] / ev[0]
        print(f"[diag 族] M={M:g}: Λ_H = {Lh:.6f}  （定理 0.9.4.11 预言 M²={M*M:.6f}）"
              f" {'✓' if abs(Lh - M*M) < 1e-9 else '✗'}")

    print()
    print("[OK] 零方差定律大规模验证通过" if ok else "[FAIL] 存在波动")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
