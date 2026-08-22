#!/usr/bin/env python3
"""lambda_H.py — 里程碑 1：零方差定律大规模验证（RX570 GPU）
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)

验证目标（0.9 §4.1–4.3）：
  定理 0.9.4.02 : negacyclic 无调制格 G=BB^T ⟹ Λ_H = λ_2/λ_1 ≡ 1（零方差，确定性）
  定理 0.9.4.11 : diag 格 B=diag(1,M,...,M) ⟹ Λ_H = M^2 精确
  对照          : 一般随机 A（非 negacyclic）⟹ Λ_H 波动 ≠ 1

策略（local mem 限制：Apple OpenCL gfx803 对 64x64 double 矩阵顶格失败）：
  - GPU 批量：d=16（G 32x32，8KB local——满血）
  - numpy 补充：d=32（G 64x64）N=512（理论断言与 d 无关，补充确认）

用法：
  python3 lambda_H.py verify   # 小规模验证（GPU d=16 + numpy d=32 + diag）
  python3 lambda_H.py full     # 全量：GPU d=16 N=10^5 + numpy d=32 N=512 + 对照
"""
import os
import sys
import time

import numpy as np
import pyopencl as cl

from batch_jacobi import get_gpu, build_program

HERE = os.path.dirname(os.path.abspath(__file__))


def build_gram(ctx, d, q, mode=0):
    src = open(os.path.join(HERE, "gram_kernel.cl")).read()
    return cl.Program(ctx, src).build(f"-DNEG_D={d} -DQMOD={q}")


def gen_gram_gpu(ctx, queue, gprog, mats, n, mode=0):
    """生成 mats 个 G 矩阵（2d x 2d，mode=0 negacyclic / 1 general-random）
    返回 READ_WRITE buffer（供 batch_jacobi 复用）"""
    buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, mats * n * n * 8)
    wg = 256
    gprog.gen_gram(queue, (mats * wg,), (wg,), buf, np.int32(mats), np.int32(mode))
    return buf


def gen_G_numpy(d, q, N, mode=0, seed=20260822):
    """numpy 参考实现：negacyclic(mode=0)/一般随机(mode=1) A → G = [[AA^T+I, qI],[qI, q^2 I]]"""
    rng = np.random.default_rng(seed)
    ii, jj = np.meshgrid(np.arange(d), np.arange(d), indexing="ij")
    idx = (jj - ii) % d
    sign = np.where(jj < ii, -1.0, 1.0)
    Gs = np.empty((N, 2 * d, 2 * d))
    for t in range(N):
        if mode == 0:
            a = rng.integers(0, q, d).astype(np.float64)
            A = a[idx] * sign
        else:
            A = rng.integers(0, q, (d, d)).astype(np.float64)
        AA = A @ A.T
        G = np.empty((2 * d, 2 * d))
        G[:d, :d] = AA + np.eye(d)
        G[:d, d:] = np.eye(d) * q
        G[d:, :d] = np.eye(d) * q
        G[d:, d:] = np.eye(d) * q * q
        Gs[t] = G
    return Gs


def stats(name, lam, off=None):
    """Λ_H 统计摘要"""
    mean = float(np.mean(lam))
    std = float(np.std(lam))
    mn, mx = float(np.min(lam)), float(np.max(lam))
    dev = float(np.max(np.abs(lam - 1.0)))
    print(f"[{name}] N={len(lam)}  mean={mean:.10f}  std={std:.3e}  "
          f"min={mn:.10f}  max={mx:.10f}  max|Λ_H-1|={dev:.3e}")
    if off is not None:
        print(f"         <offdiag²>={float(np.mean(off)):.3e}（收敛质量）")
    return mean, std, dev


def verify(ctx_queue, N=256, q=3329):
    """GPU d=16 numpy 对照 + numpy d=32 补充 + diag 对照"""
    ctx, queue, dev = ctx_queue
    print(f"[VERIFY] N={N}，q={q}")
    all_ok = True

    # ---- GPU d=16：numpy 对照（拷贝回 G 独立求特征值）----
    d = 16
    n = 2 * d
    gprog = build_gram(ctx, d, q, 0)
    jprog = build_program(ctx, n)
    G_buf = gen_gram_gpu(ctx, queue, gprog, N, n, mode=0)
    eig_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, N * n * 8)
    off_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, N * 8)
    wg = min(2 * n, 256)
    jprog.batch_jacobi(queue, (N * wg,), (wg,),
                       G_buf, eig_buf, off_buf, np.int32(N), np.int32(24))
    eig = np.empty((N, n), np.float64)
    cl.enqueue_copy(queue, eig, eig_buf)
    queue.finish()
    G = np.empty((N, n, n), np.float64)
    cl.enqueue_copy(queue, G, G_buf)
    queue.finish()
    sym_ok = float(np.max(np.abs(G - G.swapaxes(1, 2)))) < 1e-9
    pd_ok = bool(np.all(np.linalg.eigvalsh(G) > 0))
    eig_np = np.sort(np.linalg.eigvalsh(G), axis=1)
    eg = np.sort(eig, axis=1)
    err = float(np.max(np.abs(eg - eig_np)))
    scale = float(np.max(np.abs(eig_np)))
    rel = err / max(1.0, scale)
    lam = eg[:, 1] / eg[:, 0]
    ok = rel < 1e-11 and sym_ok and pd_ok
    all_ok &= ok
    print(f"  GPU d={d} (G {n}x{n}): 对称={sym_ok} 正定={pd_ok}  "
          f"max|Δλ|={err:.3e} (rel={rel:.2e})  Λ_H mean={float(np.mean(lam)):.10f}  "
          f"std={float(np.std(lam)):.3e}  {'✓' if ok else '✗'}")
    G_buf.release(); eig_buf.release(); off_buf.release()

    # ---- numpy d=32 补充（64x64 超出 Apple OpenCL local mem 顶格，CPU 验证）----
    d = 32
    Gs = gen_G_numpy(d, q, N=256, mode=0)
    eg = np.sort(np.linalg.eigvalsh(Gs), axis=1)
    lam = eg[:, 1] / eg[:, 0]
    std = float(np.std(lam))
    ok = std < 1e-9
    all_ok &= ok
    print(f"  numpy d={d} (G {2*d}x{2*d}): Λ_H mean={float(np.mean(lam)):.10f}  "
          f"std={std:.3e}  {'✓' if ok else '✗'}")

    # ---- diag 对照（定理 0.9.4.11）----
    all_ok &= diag_control(ctx_queue)
    print(f"[VERIFY] {'全部通过' if all_ok else '存在失败'}")
    return all_ok


def diag_control(ctx_queue, N=4096, M=10.0, n=32):
    """定理 0.9.4.11：B=diag(1,M,...,M)，G=diag(1,M^2,...,M^2)，Λ_H=M^2 精确零方差"""
    ctx, queue, dev = ctx_queue
    jprog = build_program(ctx, n)
    G = np.tile(np.eye(n), (N, 1, 1))
    G[:, 0, 0] = 1.0
    for i in range(1, n):
        G[:, i, i] = M * M
    A_flat = np.ascontiguousarray(G).reshape(N * n * n)
    G_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=A_flat)
    eig_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, N * n * 8)
    off_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, N * 8)
    wg = min(2 * n, 256)
    jprog.batch_jacobi(queue, (N * wg,), (wg,),
                       G_buf, eig_buf, off_buf, np.int32(N), np.int32(24))
    eig = np.empty((N, n), np.float64)
    cl.enqueue_copy(queue, eig, eig_buf)
    queue.finish()
    e = np.sort(eig, axis=1)
    lam = e[:, 1] / e[:, 0]
    exp = M * M
    dev = float(np.max(np.abs(lam - exp)))
    std = float(np.std(lam))
    print(f"[diag 对照 定理0.9.4.11] B=diag(1,{M:.0f},...,{M:.0f})  N={N}")
    print(f"  Λ_H mean={float(np.mean(lam)):.6f}（期望 {exp:.6f} = M²）  "
          f"std={std:.3e}  max|Λ_H-M²|={dev:.3e}  {'✓ 精确' if dev < 1e-9 else '✗'}")
    return dev < 1e-9


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    ctx, queue, dev = get_gpu()
    print(f"[DEVICE] {dev.name}")

    if mode == "verify":
        ok = verify(ctx_queue=(ctx, queue, dev))
        print("[OK] 验证通过，可以跑全量" if ok else "[FAIL] 验证失败")
        return 0 if ok else 1

    if mode == "full":
        q = 3329
        # 1) negacyclic 零方差主验证：GPU d=16 N=10^5
        lam, off, dt = run_lambda_H(16, q, N=100_000, mode=0,
                                    ctx_queue=(ctx, queue, dev))
        rate = 100_000 / dt
        print(f"--- negacyclic d=16（G 32x32）N=10^5 [GPU] ---")
        stats("negacyclic d=16", lam, off)
        print(f"  耗时 {dt:.1f}s  吞吐 {rate:.0f} mat/s")

        # 2) negacyclic 补充：numpy d=32 N=512
        t0 = time.perf_counter()
        Gs = gen_G_numpy(32, q, N=512, mode=0)
        eg = np.sort(np.linalg.eigvalsh(Gs), axis=1)
        lam = eg[:, 1] / eg[:, 0]
        dt = time.perf_counter() - t0
        print(f"--- negacyclic d=32（G 64x64）N=512 [numpy 补充] ---")
        stats("negacyclic d=32", lam)
        print(f"  耗时 {dt:.1f}s")

        # 3) diag 对照
        diag_control(ctx_queue=(ctx, queue, dev))

        # 4) 一般随机对照
        lam, off, dt = run_lambda_H(16, q, N=2048, mode=1,
                                    ctx_queue=(ctx, queue, dev))
        print("--- 一般随机对照（非 negacyclic）d=16 N=2048 [GPU] ---")
        stats("random d=16", lam, off)
        print(f"  耗时 {dt:.1f}s")
        return 0

    print(f"未知模式: {mode}")
    return 1


def run_lambda_H(d, q, N, mode=0, batch=1024, sweeps=24, ctx_queue=None):
    """批量计算 Λ_H = λ_2/λ_1。返回 (lam (N,), offdiag (N,), 耗时)"""
    n = 2 * d
    if ctx_queue is None:
        ctx, queue, dev = get_gpu()
    else:
        ctx, queue, dev = ctx_queue
    gprog = build_gram(ctx, d, q, mode)
    jprog = build_program(ctx, n)
    mf = cl.mem_flags

    lam_all = np.empty(N, np.float64)
    off_all = np.empty(N, np.float64)
    wg = min(2 * n, 256)

    t0 = time.perf_counter()
    for start in range(0, N, batch):
        m = min(batch, N - start)
        G_buf = gen_gram_gpu(ctx, queue, gprog, m, n, mode)
        eig_buf = cl.Buffer(ctx, mf.WRITE_ONLY, m * n * 8)
        off_buf = cl.Buffer(ctx, mf.WRITE_ONLY, m * 8)
        jprog.batch_jacobi(queue, (m * wg,), (wg,),
                           G_buf, eig_buf, off_buf,
                           np.int32(m), np.int32(sweeps))
        eig = np.empty((m, n), np.float64)
        off = np.empty(m, np.float64)
        cl.enqueue_copy(queue, eig, eig_buf)
        cl.enqueue_copy(queue, off, off_buf)
        queue.finish()
        e = np.sort(eig, axis=1)
        lam_all[start:start + m] = e[:, 1] / e[:, 0]
        off_all[start:start + m] = off
        G_buf.release(); eig_buf.release(); off_buf.release()
    dt = time.perf_counter() - t0
    return lam_all, off_all, dt


if __name__ == "__main__":
    raise SystemExit(main())
