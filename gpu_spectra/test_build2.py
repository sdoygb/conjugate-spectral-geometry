#!/usr/bin/env python3
"""test_build2.py — 找 __local 大数组的编译尺寸阈值（Apple AMD GPU）"""
import re
import pyopencl as cl

SRC = open("negacyclic_kernel.cl").read()

platforms = cl.get_platforms()
gpu = None
for p in platforms:
    for dd in p.get_devices():
        if dd.type == cl.device_type.GPU:
            gpu = dd
            break
    if gpu:
        break
ctx = cl.Context([gpu])
print(f"[DEVICE] {gpu.name}")
print(f"[LOCAL MEM SIZE] {gpu.local_mem_size} bytes")

for nmax in (64, 56, 48, 44, 40, 36, 32, 24):
    src = SRC.replace("#define NMAX 64", f"#define NMAX {nmax}")
    kb = nmax * nmax * 8 / 1024
    try:
        cl.Program(ctx, src).build()
        print(f"[NMAX={nmax:2d}] A={kb:6.1f}KB  BUILD OK")
    except Exception as e:
        msg = str(e)
        tag = "SC failed" if "SC failed" in msg else "其他错误"
        print(f"[NMAX={nmax:2d}] A={kb:6.1f}KB  BUILD FAIL: {tag}")
