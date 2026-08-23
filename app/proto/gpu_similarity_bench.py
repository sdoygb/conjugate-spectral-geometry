#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU 原型验证：RX 570 vs CPU 全对全矩阵乘加速比实测
验证"多对多交叉验证"最核心的计算：C = A @ A^T 的 cosine 相似度矩阵。
规模从小到大演示 GPU 何时开始反超 CPU。
"""
import os
os.environ.setdefault("PYOPENCL_NO_CACHE", "1")
import sys
import time
import numpy as np
import pyopencl as cl


def pick_gpu():
    pl = cl.get_platforms()[0]
    for d in pl.get_devices():
        if d.name and "Radeon" in d.name:
            return d
    return pl.get_devices()[0]


def cpu_matmul(A, B):
    t0 = time.perf_counter()
    C = A @ B
    dt = time.perf_counter() - t0
    return C, dt


def gpu_kernel(ctx, queue):
    """编译一次矩阵乘内核(复用)。"""
    return cl.Program(ctx, """
        __kernel void mm(__global const float* A, __global const float* B,
                         __global float* C, int K, int C_width) {
            int r = get_global_id(0);
            int c = get_global_id(1);
            float acc = 0.0f;
            for (int i = 0; i < K; ++i)
                acc += A[r*K + i] * B[i*C_width + c];
            C[r*C_width + c] = acc;
        }
    """).build().mm


def run_gpu(prg_mm, queue, A_c, B_c, C_c, k, n):
    prg_mm(queue, (n, n), None, A_c, B_c, C_c, np.int32(k), np.int32(n))
    queue.finish()


def bench(N, dim, ctx, queue, prg_mm):
    """CPU(NxN)、GPU含传输、GPU纯内核 三段计时；全对全 A@A^T。"""
    A_cpu = np.random.rand(N, dim).astype(np.float32)
    A_cpu_T = np.ascontiguousarray(A_cpu.T)
    A_gpu = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, A_cpu.nbytes)
    B_gpu = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, A_cpu_T.nbytes)
    cl._enqueue_write_buffer(queue, A_gpu, A_cpu)
    cl._enqueue_write_buffer(queue, B_gpu, A_cpu_T)
    C_gpu = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, np.dtype(np.float32).itemsize * N * N)
    C_cpu_read = np.empty((N, N), dtype=np.float32)

    # CPU
    C_cpu, dt_cpu = cpu_matmul(A_cpu, A_cpu_T)

    # GPU 含传输(上传A/B + 内核 + 回读C)
    t0 = time.perf_counter()
    cl._enqueue_write_buffer(queue, A_gpu, A_cpu)
    cl._enqueue_write_buffer(queue, B_gpu, A_cpu_T)
    run_gpu(prg_mm, queue, A_gpu, B_gpu, C_gpu, dim, N)
    cl._enqueue_read_buffer(queue, C_gpu, C_cpu_read)
    queue.finish()
    dt_gpu_total = time.perf_counter() - t0

    # GPU 纯内核(数据已在显存，仅计时内核)
    t0 = time.perf_counter()
    for _ in range(3):
        run_gpu(prg_mm, queue, A_gpu, B_gpu, C_gpu, dim, N)
    dt_gpu_kernel = (time.perf_counter() - t0) / 3

    # 校验
    cl._enqueue_read_buffer(queue, C_gpu, C_cpu_read)
    queue.finish()
    err = float(np.max(np.abs(C_cpu - C_cpu_read)))
    return dt_cpu, dt_gpu_total, dt_gpu_kernel, err


def gpu_kernel_tiled(ctx, queue, TILE=16):
    """分块共享内存矩阵乘：真实 GPU 矩阵乘标准优化（复用局部性）。
    维度映射：dim0=行 (lx)，dim1=列 (ly)。C 输出 (r,c)。
      As[lx][ly] = A[(rb+lx)][bk+ly]   （行=r的块，列=远端 bk+ly）
      Bs[lx][ly] = B[(bk+lx)][cb+ly]   （行=远端 bk+lx，列=c的块）
      acc += As[lx][kk] * Bs[kk][ly]
    """
    t = TILE
    return cl.Program(ctx, f"""
        #define TS {t}
        __kernel void mm_tiled(__global const float* A, __global const float* B,
                               __global float* C, int K, int N) {{
            __local float As[TS][TS];
            __local float Bs[TS][TS];
            int lx = get_local_id(0), ly = get_local_id(1);
            int r = get_global_id(0), c = get_global_id(1);
            int rb = (r / TS) * TS, cb = (c / TS) * TS;
            float acc = 0.0f;
            for (int bk = 0; bk < K; bk += TS) {{
                int a_col = bk + ly, b_row = bk + lx;
                As[lx][ly] = (a_col < K) ? A[(rb + lx)*K + a_col] : 0.0f;
                Bs[lx][ly] = (b_row < K) ? B[b_row*N + (cb + ly)] : 0.0f;
                barrier(CLK_LOCAL_MEM_FENCE);
                for (int kk = 0; kk < TS; ++kk)
                    acc += As[lx][kk] * Bs[kk][ly];
                barrier(CLK_LOCAL_MEM_FENCE);
            }}
            if (r < N && c < N) C[r*N + c] = acc;
        }}
    """).build().mm_tiled


def run_gpu_tiled(prg_tiled, queue, A_gpu, B_gpu, C_gpu, k, n, tile=32):
    local = (tile, tile)
    global_ = ((n + tile - 1) // tile * tile, (n + tile - 1) // tile * tile)
    prg_tiled(queue, global_, local, A_gpu, B_gpu, C_gpu, np.int32(k), np.int32(n))
    queue.finish()


def bench_tiled(N, dim, ctx, queue, prg_tiled, tile=16):
    """公平对比 GPU 分块矩阵乘（含传输 / 纯内核） vs CPU。"""
    A_cpu = np.random.rand(N, dim).astype(np.float32)
    A_cpu_T = np.ascontiguousarray(A_cpu.T)
    A_gpu = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, A_cpu.nbytes)
    B_gpu = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, A_cpu_T.nbytes)
    C_gpu = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, np.dtype(np.float32).itemsize * N * N)
    C_cpu_read = np.empty((N, N), dtype=np.float32)
    cl._enqueue_write_buffer(queue, A_gpu, A_cpu)
    cl._enqueue_write_buffer(queue, B_gpu, A_cpu_T)
    queue.finish()

    C_cpu, dt_cpu = cpu_matmul(A_cpu, A_cpu_T)

    t0 = time.perf_counter()
    run_gpu_tiled(prg_tiled, queue, A_gpu, B_gpu, C_gpu, dim, N, tile)
    cl._enqueue_read_buffer(queue, C_gpu, C_cpu_read)
    queue.finish()
    dt_total = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(3):
        run_gpu_tiled(prg_tiled, queue, A_gpu, B_gpu, C_gpu, dim, N, tile)
    dt_kernel = (time.perf_counter() - t0) / 3

    cl._enqueue_read_buffer(queue, C_gpu, C_cpu_read)
    queue.finish()
    err = float(np.max(np.abs(C_cpu - C_cpu_read)))
    return dt_cpu, dt_total, dt_kernel, err


if __name__ == "__main__":
    dev = pick_gpu()
    print(f"[GPU] 使用设备: {dev.name} ({dev.global_mem_size/1e9:.1f} GB, {dev.max_compute_units} CU)")
    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
    prg_tiled = gpu_kernel_tiled(ctx, queue, 16)
    queue.finish()
    print()

    print("需要分块(共享内存)内核公平对比 CPU numpy。")
    print("GPU分块内核 | 全局事务过大请在下面观察(此内核已用 Tile=32 共享内存优化):\n")
    print(f"{'规模(N×N)':<14}{'CPU(s)':<10}{'GPU总(s)':<10}{'GPU核心(s)':<11}{'加速比≈':<10}{'误差':<10}")
    print("-" * 70)
    for N, dim in [(256, 1024), (1024, 1024), (2048, 1024), (3444, 1024), (4096, 1024)]:
        dt_cpu, dt_total, dt_kernel, err = bench_tiled(N, dim, ctx, queue, prg_tiled)
        sp_total = dt_cpu / dt_total
        sp_kernel = dt_cpu / dt_kernel
        print(f"N={N:<7}{dt_cpu:8.4f}  {dt_total:8.4f}  {dt_kernel:9.4f}   "
              f"{sp_total:4.1f}/{sp_kernel:5.1f}x   {err:.2e}")
    print("\n进比分：GPU总(含传输)/GPU核心(纯算力). 注：N=3444 是当前中间层真实 chunk 数基底。")