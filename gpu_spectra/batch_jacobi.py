#!/usr/bin/env python3
"""batch_jacobi.py — 批量 Jacobi 特征值：GPU kernel + numpy 对照验证
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
里程碑 0.5：批量实对称特征值 kernel 正确性验证
"""
import os
import time

import numpy as np
import pyopencl as cl

HERE = os.path.dirname(os.path.abspath(__file__))


def get_gpu():
    platform = cl.get_platforms()[0]
    devices = platform.get_devices()
    gpu = [d for d in devices if d.type == cl.device_type.GPU]
    dev = gpu[0] if gpu else devices[0]
    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx)
    return ctx, queue, dev


def build_program(ctx, n):
    src = open(os.path.join(HERE, "jacobi_kernel.cl")).read()
    return cl.Program(ctx, src).build(f"-DMAT_N={n}")


def batch_jacobi_gpu(ctx, queue, prog, A_batch, max_sweeps=24):
    """A_batch: (mats, n, n) float64 实对称
    返回 (eigvals (mats,n) 未排序, offdiag_sq (mats,))
    """
    mats, n, _ = A_batch.shape
    A_flat = np.ascontiguousarray(A_batch).reshape(mats * n * n)
    mf = cl.mem_flags
    A_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=A_flat)
    eig_buf = cl.Buffer(ctx, mf.WRITE_ONLY, mats * n * 8)
    off_buf = cl.Buffer(ctx, mf.WRITE_ONLY, mats * 8)
    wg = min(2 * n, 256)  # work-group size = 2n（旋转应用满并行）
    prog.batch_jacobi(queue, (mats * wg,), (wg,),
                      A_buf, eig_buf, off_buf,
                      np.int32(mats), np.int32(max_sweeps))
    eig = np.empty((mats, n), np.float64)
    off = np.empty(mats, np.float64)
    cl.enqueue_copy(queue, eig, eig_buf)
    cl.enqueue_copy(queue, off, off_buf)
    queue.finish()
    return eig, off


def check(name, A, eig_gpu, off, tol=1e-9):
    """排序后逐元素比对 numpy 特征值"""
    eig_np = np.linalg.eigvalsh(A)
    eg = np.sort(eig_gpu, axis=1)
    en = np.sort(eig_np, axis=1)
    err = float(np.max(np.abs(eg - en)))
    conv = float(np.mean(off))
    ok = err < tol
    print(f"[{name}] max|Δλ|={err:.3e}  <offdiag²>={conv:.3e}  "
          f"PASS={ok}  {'✓' if ok else '✗'}")
    return ok


def main():
    ctx, queue, dev = get_gpu()
    print(f"[DEVICE] {dev.name}  (max WG={dev.max_work_group_size})")
    rng = np.random.default_rng(42)
    all_ok = True

    # ---- 测试1-3：随机对称矩阵 X+X^T，n=8/16/32 ----
    for n in (8, 16, 32):
        prog = build_program(ctx, n)
        mats = 512
        X = rng.standard_normal((mats, n, n))
        A = X + X.swapaxes(1, 2)

        t0 = time.perf_counter()
        eig_gpu, off = batch_jacobi_gpu(ctx, queue, prog, A)
        dt = time.perf_counter() - t0

        ok = check(f"N={n:2d} 随机对称 {mats}批", A, eig_gpu, off)
        all_ok &= ok
        print(f"       GPU {dt * 1000:7.1f} ms  ({mats / dt / 1e3:7.2f}k mat/s)")

    # ---- 测试4：SPD 矩阵 X X^T（格 Gram 矩阵同结构），n=32 ----
    n = 32
    prog = build_program(ctx, n)
    mats = 512
    X = rng.standard_normal((mats, n, n)) * 0.3
    A = X @ X.swapaxes(1, 2) + np.eye(n) * 0.01  # SPD：特征值>0
    eig_gpu, off = batch_jacobi_gpu(ctx, queue, prog, A)
    ok = check(f"N=32 SPD(Gram型) {mats}批", A, eig_gpu, off)
    all_ok &= ok

    # ---- 测试5：近对角矩阵（扰动 1e-6）——Jacobi 快速收敛路径 ----
    n = 16
    prog = build_program(ctx, n)
    mats = 256
    D = rng.uniform(0.5, 2.0, (mats, n))
    eps = rng.standard_normal((mats, n, n)) * 1e-6
    A = np.zeros((mats, n, n))
    for i in range(n):
        A[:, i, i] = D[:, i]
    A = A + eps + eps.swapaxes(1, 2)
    eig_gpu, off = batch_jacobi_gpu(ctx, queue, prog, A)
    ok = check(f"N=16 近对角 {mats}批", A, eig_gpu, off)
    all_ok &= ok

    print()
    print("[OK] 批量 Jacobi kernel 全部验证通过" if all_ok
          else "[FAIL] 存在未通过的测试")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
