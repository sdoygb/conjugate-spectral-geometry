#!/usr/bin/env python3
"""test_build.py — 二分定位 Apple OpenCL "SC failed" 编译失败原因（强制 GPU）"""
import re
import pyopencl as cl

SRC = open("negacyclic_kernel.cl").read()

variants = {}
variants["A_full"] = SRC

# B: 去掉 Jacobi
m = re.search(r"    /\* ---- 3\. cyclic Jacobi", SRC)
m2 = re.search(r"    /\* ---- 4\. 提取两个最小特征值", SRC)
variants["B_no_jacobi"] = SRC[:m.start()] + SRC[m2.start():]

# C: PCG32 → 简单 LCG
variants["C_lcg"] = SRC.replace(
    """inline uint pcg32(uint *s) {
    uint state = *s;
    *s = state * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}""",
    """inline uint pcg32(uint *s) {
    *s = *s * 1664525u + 1013904223u;
    return *s;
}""")

# D: pcg32 内联展开
variants["D_inline_expand"] = SRC.replace(
    "uint r = pcg32(&rng);",
    "uint st = rng; rng = st * 747796405u + 2891336453u; "
    "uint w = ((st >> ((st >> 28u) + 4u)) ^ st) * 277803737u; "
    "uint r = (w >> 22u) ^ w;")

# E: 去掉 __local double A[NMAX*NMAX] 大数组（改用小数组）
srcE = SRC.replace("__local double A[NMAX * NMAX];",
                   "__local double A[16 * 16];")
variants["E_small_local"] = srcE

# 选 GPU 设备
platforms = cl.get_platforms()
gpu = None
for p in platforms:
    for dd in p.get_devices():
        if dd.type == cl.device_type.GPU:
            gpu = dd
            break
    if gpu:
        break
if gpu is None:
    print("NO GPU DEVICE"); raise SystemExit(1)
ctx = cl.Context([gpu])
print(f"[DEVICE] {gpu.name}\n")

for name, src in variants.items():
    try:
        cl.Program(ctx, src).build()
        print(f"[{name}] BUILD OK")
    except Exception as e:
        msg = str(e)
        lines = [l for l in msg.splitlines() if "error" in l.lower()]
        if lines:
            print(f"[{name}] BUILD FAIL: {' | '.join(lines[-3:])}")
        elif "SC failed" in msg:
            print(f"[{name}] BUILD FAIL: SC failed (编译器内部错误)")
        else:
            print(f"[{name}] BUILD FAIL: {msg.splitlines()[-1]}")
