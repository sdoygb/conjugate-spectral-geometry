#!/usr/bin/env python3
"""补丁2：kernel 改用固定大小 local 数组（绕开 pyopencl 动态 local 传参问题）"""

# ---- 1. 改 kernel：去掉动态 lmem 参数，固定 local 数组 ----
kp = 'gpu_spectra/lattice_kernel.cl'
ksrc = open(kp).read()

old_k = """    const int max_sweeps,
    __local double* lmem)           /* 动态 local：G + A */
{"""
new_k = """    const int max_sweeps)
{
    /* 固定 local：d<=32 时 G(64x64)=32KB + A(32x32)=4KB = 36KB < 64KB LDS */
    __local double G[64 * 64];
    __local int A[32 * 32];"""
assert old_k in ksrc
ksrc = ksrc.replace(old_k, new_k)

old_k2 = """    __local double* G = (__local double*)lmem;
    __local int* A = (__local int*)(lmem + n * n);
    __local int lp, lq, lskip, lconv;"""
new_k2 = """    __local int lp, lq, lskip, lconv;"""
assert old_k2 in ksrc
ksrc = ksrc.replace(old_k2, new_k2)
open(kp, 'w').write(ksrc)

# ---- 2. 改 py：去掉 None/local_bytes 传参 ----
pp = 'gpu_spectra/lattice_lambdaH.py'
psrc = open(pp).read()

old_p = """    local_bytes = n * n * 8 + d * d * 4
    wg = n
    prog.lattice_lambdaH(queue, (N * wg,), (wg,),
                         seed_buf, np.int32(d), np.float64(Q), np.int32(mode),
                         m1_buf, m2_buf, np.int32(nsweeps),
                         None, local_bytes)"""
new_p = """    assert d <= 32, "kernel 固定 local 数组支持 d<=32"
    wg = n
    prog.lattice_lambdaH(queue, (N * wg,), (wg,),
                         seed_buf, np.int32(d), np.float64(Q), np.int32(mode),
                         m1_buf, m2_buf, np.int32(nsweeps))"""
assert old_p in psrc
psrc = psrc.replace(old_p, new_p)
open(pp, 'w').write(psrc)
print("patched2 OK")
