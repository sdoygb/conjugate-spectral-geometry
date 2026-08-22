"""GPU 冒烟测试：验证 RX570 OpenCL 管线 + FP64 支持探测。
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
"""
import time
import numpy as np
import pyopencl as cl

# ---- 设备选择：优先 GPU ----
platform = cl.get_platforms()[0]
devices = platform.get_devices()
gpu = [d for d in devices if d.type == cl.device_type.GPU]
cpu = [d for d in devices if d.type == cl.device_type.CPU]
dev = gpu[0] if gpu else cpu[0]
print(f"[DEVICE] {dev.name} | CU={dev.max_compute_units} | WG={dev.max_work_group_size}")

ctx = cl.Context([dev])
queue = cl.CommandQueue(ctx)

# ---- FP64 探测：macOS OpenCL 1.2 上 AMD 的双精度是扩展，必须实测 ----
fp64 = False
try:
    prg64 = cl.Program(ctx, """
    __kernel void dadd(__global double *x) { x[get_global_id(0)] += 1.0; }
    """).build()
    fp64 = True
    print("[FP64] double kernel 编译通过 → GPU 支持双精度")
except Exception as e:
    print(f"[FP64] double kernel 编译失败 → 只能用 float：{str(e)[:120]}")

# ---- axpy 冒烟：y = 2x + y，16M float = 64MB ----
n = 1 << 24
x = np.random.rand(n).astype(np.float32)
y = np.zeros(n, dtype=np.float32)
x_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=x)
y_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR, hostbuf=y)

prg = cl.Program(ctx, """
__kernel void axpy(__global const float *x, __global float *y,
                   const float a, const int n) {
    int i = get_global_id(0);
    if (i < n) y[i] = a * x[i] + y[i];
}
""").build()

t0 = time.time()
prg.axpy(queue, (n,), None, x_buf, y_buf, np.float32(2.0), np.int32(n))
queue.finish()
t1 = time.time()
cl.enqueue_copy(queue, y, y_buf).wait()

err = float(np.max(np.abs(y - 2.0 * x)))
gbs = 2 * n * 4 / (t1 - t0) / 1e9
print(f"[AXPY] n={n} ({64} MB) 耗时 {t1-t0:.4f}s  带宽 {gbs:.1f} GB/s  max_err={err:.2e}")
print("[SMOKE]", "PASS" if err < 1e-4 else "FAIL")
