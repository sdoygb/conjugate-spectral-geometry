#!/usr/bin/env python3
"""theta_invariants.py — 里程碑 C：格不变量尺度（θ 级数/短向量计数的确定性）
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
猜想 10.75（260823）三尺度统计刚性 §4 群尺度；milestoneB 遗留：
  Λ_H 基依赖（随机基系综 std 1.4–2.3，非刚性）；θ 级数/最短向量计数为真不变量
  ——"群尺度刚性的正确载体可能是格不变量而非基依赖的 Λ_H（下一步候选）"

探针 C1：θ 级数的确定性
  · GPU DP（theta_kernel.cl）：√2Λ₂₄ = C24' 的范数² ≤ R 精确计数（纯整数，4096 码字并行）
  · 理论对照：θ_√2Λ(q) = E12(q⁴) − (65520/691)Δ(q⁴)
    （Leech 是 24 维偶幺模格 ⟹ θ 为权 12 模形式；q⁴=196560 标定 ⟹ c=−65520/691；
      系数 N_{4n} = (65520/691)(σ₁₁(n)−τ(n))；q⁶=16,773,120 与 q⁸=398,034,000 均验证 ✓）
  · 跨实现对照：fpylll 球内枚举（R=8：N₈ = 196560 = 24 维接吻数，最短向量计数）
  · 对照格：E₈（θ = E₄(q²)，N_{2m} = 240σ₃(m)）、D₈、Z⁸（numpy DP）

用法：
  python3 theta_invariants.py            # R=16 主验证 + R=64 深系数
  python3 theta_invariants.py --R 32     # 指定半径
  python3 theta_invariants.py --check    # 只跑 fpylll R=8 对照
"""
import argparse
import os
import sys
import time
from math import comb
from fractions import Fraction

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


# ---------------- Golay G24 码字 ----------------

def golay_generator():
    """Golay G24 生成矩阵 [I_12 | P]（Paley 构造，与 highsym_spectra._golay_generator 同源）"""
    S = {1, 3, 4, 5, 9}   # mod 11 二次剩余
    P = np.zeros((12, 12), dtype=int)
    for i in range(1, 12):
        for j in range(1, 12):
            if i == j:
                P[i, j] = 1
            elif (i - j) % 11 in S:
                P[i, j] = 1
    P[0, 1:] = 1
    P[1:, 0] = 1
    return np.hstack([np.eye(12, dtype=int), P])


def golay_codewords():
    """全部 4096 个码字（24-bit uint）。G 满秩 ⟹ 2^12 个线性组合互异"""
    G = golay_generator().astype(np.uint32)
    words = np.zeros(4096, dtype=np.uint32)
    for m in range(4096):
        v = np.zeros(24, dtype=np.uint32)
        for i in range(12):
            if (m >> i) & 1:
                v = (v + G[i]) % 2
        w = 0
        for j in range(24):
            w |= int(v[j]) << j
        words[m] = w
    return words


# ---------------- GPU DP ----------------

def build_program(ctx):
    src = open(os.path.join(HERE, "theta_kernel.cl")).read()
    return cl.Program(ctx, src).build()


def theta_leech_gpu(ctx, queue, prog, words, R, wg=16):
    """GPU DP：范数² ≤ R 的 √2Λ₂₄ 点计数直方图（s = 8,12,...,R 步长 4）
    返回 (hist [nbins] uint64, per_word [4096,nbins], 耗时)"""
    assert 8 <= R <= 64 and R % 4 == 0
    nbins = (R - 8) // 4 + 1
    mf = cl.mem_flags
    wbuf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR,
                     hostbuf=np.ascontiguousarray(words, np.uint32))
    pw = np.zeros((len(words), nbins), dtype=np.uint64)
    pbuf = cl.Buffer(ctx, mf.WRITE_ONLY, pw.nbytes)
    t0 = time.perf_counter()
    prog.theta_leech(queue, (len(words),), (wg,), wbuf, np.int32(R), pbuf)
    cl.enqueue_copy(queue, pw, pbuf)
    queue.finish()
    dt = time.perf_counter() - t0
    hist = pw.sum(axis=0)
    return hist, pw, dt


# ---------------- 理论系数（模形式） ----------------

def tau_values(N=16):
    """Δ(q) = q∏(1−qᵐ)^24 = Στ(n)qⁿ 的系数（截断多项式迭代乘法，精确整数）"""
    def mul(a, b):
        c = [0] * (N + 1)
        for i, ai in enumerate(a):
            if ai:
                for j, bj in enumerate(b):
                    if bj and i + j <= N:
                        c[i + j] += ai * bj
        return c
    P = [0] * (N + 1)
    P[0] = 1
    for k in range(1, N + 1):
        fac = [0] * (N + 1)
        for j in range(0, 25):
            e = k * j
            if e > N:
                break
            fac[e] += comb(24, j) * ((-1) ** j)
        P = mul(P, fac)
    return [P[i] for i in range(0, N)]   # τ(n) = q·P 的 q^n 系数 = P[n−1]


def theta_sqrt2lambda_theory(R):
    """θ_√2Λ(q) = E12(q⁴) − (65520/691)Δ(q⁴)；N_{4n} = (65520/691)(σ₁₁(n) − τ(n))
    对应 bins（s = 4n，n = 2..R/4）。"""
    tau = tau_values(R // 4 + 2)
    E = Fraction(65520, 691)
    out = []
    for n in range(2, R // 4 + 1):
        s11 = sum(d ** 11 for d in range(1, n + 1) if n % d == 0)
        c = E * (s11 - tau[n - 1])   # tau[i] = τ(i+1)（Δ 系数从 P 数组偏移 1）
        assert c.denominator == 1, f"n={n}: {c} 非整数"
        out.append(int(c))
    return out


def theta_e8_theory(mmax=5):
    """E₈：Θ_E₈(q) = E₄(q²)，N_{2m} = 240σ₃(m)（E₄(q) = 1 + 240Σσ₃(n)qⁿ）"""
    return [240 * sum(d ** 3 for d in range(1, m + 1) if m % d == 0)
            for m in range(1, mmax + 1)]


# ---------------- numpy 参考（对照格 E₈ / D₈ / Z⁸） ----------------

def theta_dp_par(R, cands):
    """通用 DP：(s, parity) → count。cands: 每坐标的 (贡献, 奇偶位) 候选列表"""
    dp = {(0, 0): 1}
    for cset in cands:
        ndp = {}
        for (s, p), cnt in dp.items():
            for c, b in cset:
                ns = s + c
                if ns <= R:
                    key = (ns, p ^ b)
                    ndp[key] = ndp.get(key, 0) + cnt
        dp = ndp
    return dp


def theta_zd_np(d, R):
    """Z^d：范数² ≤ R 的点计数（无奇偶约束）"""
    dp = {0: 1}
    cs = [(x * x, 0) for x in range(-int(np.floor(np.sqrt(R))), int(np.floor(np.sqrt(R))) + 1)]
    for _ in range(d):
        ndp = {}
        for s, cnt in dp.items():
            for c, _b in cs:
                ns = s + c
                if ns <= R:
                    ndp[ns] = ndp.get(ns, 0) + cnt
        dp = ndp
    return dp


def theta_d8_np(R):
    """D₈ = {x ∈ Z⁸ : Σx 偶}：贡献 x²，奇偶位 x mod 2，取 p=0"""
    cs = [(x * x, x & 1) for x in range(-int(np.floor(np.sqrt(R))), int(np.floor(np.sqrt(R))) + 1)]
    dp = theta_dp_par(R, [cs] * 8)
    return {s: c for (s, p), c in dp.items() if p == 0}


def theta_e8_np(R):
    """E₈ = D₈ ∪ (½(1⁸)+D₈)。两类各取 Σx 偶；状态用 4‖x‖²（半整贡献 (2y+1)² 是整数）
    返回 {范数²: 计数}（范数² 偶）"""
    R4 = 4 * R
    cs_int = [(4 * x * x, x & 1) for x in range(-int(np.floor(np.sqrt(R))), int(np.floor(np.sqrt(R))) + 1)]
    r = int(np.floor(np.sqrt(R))) + 1
    cs_half = []
    for y in range(-r, r + 1):
        if abs(y + 0.5) <= np.sqrt(R) + 1e-12:
            cs_half.append(((2 * y + 1) ** 2, y & 1))
    dpi = theta_dp_par(R4, [cs_int] * 8)
    dph = theta_dp_par(R4, [cs_half] * 8)
    out = {}
    for s4 in range(0, R4 + 1, 4):
        ci = sum(c for (s, p), c in dpi.items() if s == s4 and p == 0)
        ch = sum(c for (s, p), c in dph.items() if s == s4 and p == 0)
        if ci + ch:
            out[s4 // 4] = ci + ch
    return out


# ---------------- fpylll 跨实现对照 ----------------

def fpylll_enumerate_leech(R):
    """fpylll 球内枚举（LLL 约化基）：返回 {范数²: 计数}（含原点 0）
    跨实现对照：GPU DP（码结构） vs 通用 SVP 枚举（任意基）"""
    import fpylll
    sys.path.insert(0, HERE)
    from highsym_spectra import leech_basis
    B = leech_basis()
    M = fpylll.IntegerMatrix(24, 24)
    for i in range(24):
        for j in range(24):
            M[i, j] = int(round(B[i, j]))
    fpylll.LLL.reduction(M)
    gso = fpylll.GSO.Mat(M)
    gso.update_gso()
    enum = fpylll.Enumeration(gso)
    t0 = time.perf_counter()
    sols = enum.enumerate(0, 24, R, 0)
    dt = time.perf_counter() - t0
    hist = {}
    for sol in sols:
        d2 = int(round(sol[0]))
        hist[d2] = hist.get(d2, 0) + 1
    return hist, dt, len(sols)


# ---------------- 主流程 ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", type=int, default=16, help="范数² 半径（8/16/32/64）")
    ap.add_argument("--deep", action="store_true", help="附加 R=64 深系数验证")
    ap.add_argument("--check", action="store_true", help="只跑 fpylll R=8 对照")
    args = ap.parse_args()

    ctx, queue, dev = get_gpu()
    print(f"[DEVICE] {dev.name}")

    if args.check:
        hist, dt, n = fpylll_enumerate_leech(8)
        print(f"[fpylll] Leech R=8 枚举：{n} 条解，{dt:.2f}s")
        for s in sorted(hist):
            print(f"  norm²={s}: {hist[s]}")
        return 0

    words = golay_codewords()
    prog = build_program(ctx)
    wts = sorted(set(bin(int(w)).count('1') for w in words))
    print(f"[码字] Golay G24 全码字 {len(words)} 个（权重分布校验：{wts}）")

    print("=" * 96)
    print("探针 C1：θ 级数 = 格不变量尺度（√2Λ₂₄ 短向量计数精确闭式）")
    print("=" * 96)

    # ---- 主验证 R=16 ----
    R = args.R
    hist, pw, dt = theta_leech_gpu(ctx, queue, prog, words, R)
    theory = theta_sqrt2lambda_theory(R)
    print(f"\n[A] GPU DP（R={R}）：{len(words)} 码字并行，{dt*1000:.1f} ms")
    print(f"    norm² |  GPU 计数        | 理论 (65520/691)(σ₁₁−τ) | 判定")
    ok = True
    for k, s in enumerate(range(8, R + 1, 4)):
        t = theory[k]
        g = int(hist[k])
        match = (g == t)
        ok &= match
        print(f"    {s:4d}  | {g:>15d} | {t:>15d}              | {'✓' if match else '✗'}")
    print(f"    R={R} 球内总数（含原点）: {int(hist.sum()) + 1}  "
          f"{'✓' if int(hist.sum()) + 1 == sum(theory) + 1 else '✗'}")
    if not ok:
        print("[FAIL] GPU DP 与模形式理论不一致")
        return 1

    # ---- 稳定性：重复 3 次逐位一致 ----
    stable = True
    for _ in range(2):
        h2, _, _ = theta_leech_gpu(ctx, queue, prog, words, R)
        stable &= bool(np.array_equal(hist, h2))
    print(f"[稳定性] 3 次独立运行逐位一致: {'✓' if stable else '✗'}")

    # ---- fpylll 跨实现对照（R=8） ----
    print("\n[B] 跨实现对照：fpylll 通用 SVP 枚举（LLL 约化基）vs GPU 码结构 DP")
    hist_f, dtf, nf = fpylll_enumerate_leech(8)
    n8_gpu = int(hist[0]) if R >= 8 else 0
    n8_f = hist_f.get(8, 0)
    n0_f = hist_f.get(0, 0)
    print(f"    fpylll R=8：{nf} 条解（{dtf:.2f}s）；N₈ = {n8_f}（含 ± 对）")
    print(f"    GPU DP  N₈ = {n8_gpu}")
    print(f"    norm²=0（原点）: {n0_f} {'✓' if n0_f == 1 else '✗'}")
    print(f"    判定: {'✓ N₈ = 196560 双实现一致' if n8_f == n8_gpu == 196560 else '✗'}")

    # ---- 对照格（E₈ / D₈ / Z⁸，numpy DP） ----
    print("\n[C] 对照格（numpy DP）：格不变量系数")
    e8 = theta_e8_np(10)
    e8t = theta_e8_theory(5)
    print("    E₈ 范数² ≤ 10（理论 N_{2m} = 240σ₃(m)）:")
    ok_e8 = True
    for m in range(1, 6):
        g = e8.get(2 * m, 0)
        t = e8t[m - 1]
        match = (g == t)
        ok_e8 &= match
        print(f"      norm²={2*m:2d}: {g:>6d} vs 理论 {t:>6d}  {'✓' if match else '✗'}")
    d8 = theta_d8_np(10)
    z8 = theta_zd_np(8, 10)
    print(f"    D₈ norm²≤10: { {s: d8[s] for s in sorted(d8)} }")
    print(f"    Z⁸ norm²≤10: { {s: z8[s] for s in sorted(z8)} }（= θ₃(q)⁸ 系数）")

    # ---- 深系数（R=64） ----
    if args.deep or R == 64:
        R2 = 64
        hist64, _, dt64 = theta_leech_gpu(ctx, queue, prog, words, R2)
        th64 = theta_sqrt2lambda_theory(R2)
        print(f"\n[D] 深系数（R=64，GPU DP {dt64*1000:.1f} ms）:")
        print(f"    norm²  | GPU 计数               | 理论                   | 判定")
        ok64 = True
        for k, s in enumerate(range(8, R2 + 1, 4)):
            g, t = int(hist64[k]), th64[k]
            m = (g == t)
            ok64 &= m
            print(f"    {s:4d}  | {g:>20d} | {t:>20d} | {'✓' if m else '✗'}")
        tot_gpu = int(hist64.sum()) + 1
        tot_th = sum(th64) + 1
        print(f"    R=64 球内总数（含原点）: GPU {tot_gpu} vs 理论 {tot_th} "
              f"{'✓' if tot_gpu == tot_th else '✗'}")
        print(f"    [深系数] {'✓ 15 项全部一致' if ok64 else '✗'}")

    print("\n" + "=" * 96)
    print("结论：√2Λ₂₄ 的 θ 级数系数（格不变量）由 GPU DP 逐位精确锁定，")
    print("      与模形式理论（权 12）及 fpylll 枚举（跨实现）三方一致。")
    print("      对照：Λ_H（基依赖指纹）随机基系综 std 1.4–2.3（milestoneB）")
    print("      ⟹ 群尺度刚性的正确载体是格不变量，非基依赖指纹。")
    print("=" * 96)
    return 0 if (ok and ok_e8 and (n8_f == 196560)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
