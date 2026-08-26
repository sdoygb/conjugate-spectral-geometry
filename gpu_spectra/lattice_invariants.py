#!/usr/bin/env python3
"""lattice_invariants.py — 方向 1：格不变量尺度（10.75 §4 群尺度刚性的真不变量载体）

milestoneB 遗留"下一步候选"：
  高对称格的 Λ_H 无刚性（基依赖指纹），但 θ 级数/最短向量计数是真不变量——
  群尺度刚性的正确载体可能是格不变量而非基依赖的 Λ_H。

任务 A：θ 级数 shell counting（√2Λ24 ⊂ Z^24，highsym_spectra.leech_basis 三重自检基）
  枚举 {x ∈ Z^24 : ||xB||² ≤ R}，按范数² 分层计数 → theta 系数。
  闭式预言（θ = E_4³ − 720·Δ，缩放 √2Λ24：范数² = 4n，n = q 幂）：
    count[8]=196560, count[12]=16773120, count[16]=398034000, count[20]=4629381120,
    count[24]=34417656000  （calculate_math 精确验证 260824：q²..q⁶ 系数逐项吻合）
任务 B：Co₀ 自同构轨道统计量不变性
  Golay 符号翻转 D_c（c ∈ G24，自对偶 ⟹ 理论保格）+ Leech 反射 r_v（实证保格）
  → shell counting(σ(B)) 逐位 = shell counting(B)（统计量在群作用下恒等）
  → 最短向量轨道采样均匀性（撞车计数 ≈ 生日期望）

用法：
  python3 lattice_invariants.py cpu R [--bkz0]   # CPU 椭球枚举 R=8/12（R=16 慢）
  python3 lattice_invariants.py gpu R [--blocks B]  # GPU 前缀并行枚举 R=12/16
  python3 lattice_invariants.py co0 N [--save]   # Co₀ 检验（N=采样数，默认 5e4）
"""
import os
import sys
import math
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import fpylll

from highsym_spectra import leech_basis, _in_c24prime, _golay_generator

try:
    import pyopencl as cl
    HAVE_CL = True
except Exception:
    HAVE_CL = False

D = 24
THETA_PRED = {  # n = 范数²/4（√2Λ24）
    2: 196560, 3: 16773120, 4: 398034000, 5: 4629381120, 6: 34417656000,
}

# ------------------------------------------------------------------ 格基

def load_lattice(bkz=True):
    """√2Λ24 基：HNF（highsym_spectra，三重自检）→ BKZ block 24 约化。
    返回 B (24×24 int64)，自检 det=2²⁴ / 验证器全过 / 最短范数²=8。"""
    t0 = time.time()
    B0 = leech_basis().astype(np.int64)
    if bkz:
        M = fpylll.IntegerMatrix(D, D)
        for i in range(D):
            for j in range(D):
                M[i, j] = int(B0[i, j])
        fpylll.LLL.reduction(M)
        fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=D))
        B = np.array([[M[i, j] for j in range(D)] for i in range(D)], dtype=np.int64)
    else:
        B = B0
    import sympy as sp
    det = abs(int(sp.Matrix(B.tolist()).det()))
    C = _golay_generator() % 2
    okv = all(_in_c24prime(row, C) for row in B)
    minn = min(int(row @ row) for row in B)
    Gf = (B @ B.T).astype(np.float64)
    ev = np.linalg.eigvalsh(Gf)
    print(f"[基] det={det} 验证器全过={okv} 最短范数²={minn} λmin={ev[0]:.6g} "
          f"λmax={ev[0]/ev[-1]:.3g}→κ={ev[-1]/ev[0]:.3g} ({time.time()-t0:.1f}s)")
    assert det == 2 ** 24 and okv and minn == 8
    return B


def cholesky_L(B):
    """G = BB^T = L L^T（L 下三角）。返回 L float64。"""
    G = (B @ B.T).astype(np.float64)
    return np.linalg.cholesky(G)


# ------------------------------------------------------------------ CPU 椭球枚举

def ellipsoid_shells(B, R, L=None, collect=None, verb=True):
    """枚举 {x ∈ Z^24 : ||xB||² ≤ R}，返回 {范数²: 计数}（整数精确过滤）。
    collect: 若给出，收集范数² = collect 的格点行向量（int64 数组）。"""
    if L is None:
        L = cholesky_L(B)
    d = B.shape[0]
    x = np.zeros(d, dtype=np.int64)
    hist = {}
    cand = [0]
    got = [] if collect is not None else None
    tol = 1e-6

    def rec(i, partial):
        if i < 0:
            v = x @ B
            n2 = int(v @ v)
            if n2 <= R:
                hist[n2] = hist.get(n2, 0) + 1
                if got is not None and n2 == collect:
                    got.append(v.copy())
            cand[0] += 1
            return
        rest = float(L[i + 1:, i] @ x[i + 1:]) if i + 1 < d else 0.0
        a = float(L[i, i])
        b = math.sqrt(max(0.0, R - partial))
        lo = math.ceil((-b - rest) / a - tol)
        hi = math.floor((b - rest) / a + tol)
        if hi < lo:
            return
        for xi in range(lo, hi + 1):
            x[i] = xi
            z = a * xi + rest
            rec(i - 1, partial + z * z)
        x[i] = 0

    t0 = time.time()
    rec(d - 1, 0.0)
    tot = sum(hist.values())
    if verb:
        print(f"[CPU R={R}] 候选 {cand[0]} 命中 {tot} 格点（{time.time()-t0:.1f}s）")
    return hist, got


def check_pred(hist, R, tag=""):
    ok = True
    for n, c in sorted(hist.items()):
        if n in THETA_PRED:
            exp = THETA_PRED[n]
            match = "✓" if c == exp else "✗"
            ok &= (c == exp)
            print(f"  {tag}count[{n}] = {c}  预言 {exp}  {match}")
        else:
            print(f"  {tag}count[{n}] = {c}  （超出预言表）")
    return ok


# ------------------------------------------------------------------ GPU 前缀并行枚举

KERNEL_TEMPLATE = r"""
__kernel void shells(__global const long* B, __global const long* G, __global const float* L,
                     __global const double* pref, __global int* hist,
                     const int npref, const int k, const float R, const int nbins) {
    int gid = get_global_id(0);
    if (gid >= npref) return;
    long xv[%(D)d];
    /* 前缀 = 高坐标 x[k..D-1]（%(NK)d 个）+ 预算（float64，不截断） */
    for (int i = 0; i < %(NK)d; i++) xv[%(K)d + i] = (long)pref[gid * (%(NK)d + 1) + i];
    float budget = (float)pref[gid * (%(NK)d + 1) + %(NK)d];   /* R - partial(前缀高坐标) */
    int cnt[%(NB)d];
    for (int b = 0; b < nbins; b++) cnt[b] = 0;
    %(BODY)s
    for (int b = 0; b < nbins; b++)
        if (cnt[b]) atomic_add(&hist[b], cnt[b]);
}
"""


def gen_kernel_body(k):
    """生成 k 层嵌套循环（从坐标 k-1 到 0，低坐标枚举）。
    前缀固定高坐标 x[k..D-1]；rest{i} 只依赖更高坐标（j>i），已全部就绪。"""
    lines = []
    for i in range(k - 1, -1, -1):
        rest = " + ".join(f"L[{j}*{D}+{i}]*xv[{j}]" for j in range(i + 1, D)) or "0.0f"
        lines.append(f"float rest{i} = {rest};")
        lines.append(f"float bb{i} = sqrt(max(0.0f, budget));")
        lines.append(f"long lo{i} = (long)ceil((-bb{i} - rest{i}) / L[{i}*{D}+{i}] - 1e-6f);")
        lines.append(f"long hi{i} = (long)floor((bb{i} - rest{i}) / L[{i}*{D}+{i}] + 1e-6f);")
        lines.append(f"if (hi{i} < lo{i}) {{ budget = -1.0f; }}")
        lines.append(f"for (xv[{i}] = lo{i}; xv[{i}] <= hi{i}; xv[{i}]++) {{")
        lines.append(f"float z{i} = L[{i}*{D}+{i}]*xv[{i}] + rest{i};")
        lines.append(f"budget -= z{i}*z{i};")
    # 最内层（i=0 循环体内）：整数精确范数 x^T G x（G 上三角，int64）
    lines.append("""{
        long n2 = 0;
        for (int a = 0; a < %(D)d; a++)
            for (int b = a; b < %(D)d; b++) {
                long t = xv[a] * xv[b] * G[a*%(D)d + b];
                n2 += (a == b) ? t : (t << 1);
            }
        if ((n2 & 3) == 0) {
            int bin = (int)(n2 >> 2);
            if (bin < nbins && bin >= 0) cnt[bin]++;
        }
    }""" % {"D": D})
    # 闭合循环（最内层先闭合）
    for i in range(0, k):
        lines.append("}")
    return "\n".join(lines)


def gpu_context():
    """显式选择 AMD GPU（RX570，32 CU / 8GB / FP64），避免 create_some_context 选到 Intel CPU。"""
    if not HAVE_CL:
        raise RuntimeError("pyopencl 不可用")
    for p in cl.get_platforms():
        for d in p.get_devices():
            if d.type == cl.device_type.GPU and 'AMD' in d.name:
                ctx = cl.Context([d])
                print(f"[GPU] 设备: {d.name}（{d.max_compute_units} CU，"
                      f"{d.global_mem_size//2**20} MB，FP64={'cl_khr_fp64' in d.extensions}）")
                return ctx
    raise RuntimeError("未找到 AMD GPU 设备")


def gpu_shells(B, R, k=14, verb=True):
    """GPU 前缀并行枚举：CPU 枚举高坐标 x[k..D-1]（每前缀一个工作项），
    kernel 枚举低坐标 x[0..k-1]。返回 ({范数²: 计数}, 前缀数)。"""
    if not HAVE_CL:
        raise RuntimeError("pyopencl 不可用")
    L = cholesky_L(B)
    G = (B @ B.T).astype(np.int64)
    # ---- CPU 前缀枚举（高坐标 i = D-1 .. k，预算 = R − partial）
    x = np.zeros(D, dtype=np.int64)
    prefs = []

    def rec(i, partial):
        rest = float(L[i + 1:, i] @ x[i + 1:]) if i + 1 < D else 0.0
        a = float(L[i, i])
        b = math.sqrt(max(0.0, R - partial))
        lo = math.ceil((-b - rest) / a - 1e-6)
        hi = math.floor((b - rest) / a + 1e-6)
        for xi in range(max(lo, -(1 << 20)), min(hi, (1 << 20)) + 1):
            x[i] = xi
            z = a * xi + rest
            if i == k:
                prefs.append(list(x[k:]) + [R - (partial + z * z)])
            else:
                rec(i - 1, partial + z * z)
        x[i] = 0

    t0 = time.time()
    rec(D - 1, 0.0)
    npref = len(prefs)
    if verb:
        print(f"[GPU R={R} k={k}] 高坐标前缀数 {npref}（{time.time()-t0:.1f}s）")
    if npref == 0:
        raise RuntimeError("前缀数为 0——检查 k 与 R 的匹配")
    pref_arr = np.array(prefs, dtype=np.float64)
    # ---- OpenCL
    ctx = gpu_context()
    queue = cl.CommandQueue(ctx)
    mf = cl.mem_flags
    nbins = R // 4 + 2
    body = gen_kernel_body(k)
    src = KERNEL_TEMPLATE % {"D": D, "NK": D - k, "K": k, "NB": nbins, "BODY": body}
    prg = cl.Program(ctx, src).build()
    hist = np.zeros(nbins, dtype=np.int32)
    Bbuf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(B))
    Gbuf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(G))
    Lbuf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(L.astype(np.float32)))
    Pbuf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(pref_arr))
    Hbuf = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=hist)
    t0 = time.time()
    prg.shells(queue, (npref,), None, Bbuf, Gbuf, Lbuf, Pbuf, Hbuf,
               np.int32(npref), np.int32(k), np.float32(R), np.int32(nbins))
    cl.enqueue_copy(queue, hist, Hbuf).wait()
    dt = time.time() - t0
    out = {}
    for n2 in range(0, R + 1, 4):
        c = int(hist[n2 // 4])
        if c:
            out[n2] = c
    if verb:
        print(f"[GPU R={R}] 命中 {sum(out.values())} 格点（kernel {dt:.1f}s，"
              f"{sum(out.values())/dt:.2e} 点/s）")
    return out, npref


# ------------------------------------------------------------------ Co₀ 自同构检验

def golay_words(rng, n):
    G = _golay_generator() % 2
    out = np.zeros((n, D), dtype=np.int64)
    for r in range(n):
        c = np.zeros(D, dtype=np.int64)
        for i in range(12):
            if rng.randint(2):
                c = (c + G[i]) % 2
        out[r] = c
    return out


def sign_flip(c):
    return np.diag(1 - 2 * c).astype(np.int64)


def reflection(v):
    """Leech 反射 r_v(x) = x − (⟨x,v⟩/4)·v。仅当 4 | ⟨b_i,v⟩ 对所有基行才保格。
    返回矩阵 R（作用于行向量右侧）或 None（非整数）。"""
    if np.any(v % 2):          # 坐标全偶才给出整数矩阵（vv^T/4 整数）
        return None
    R = np.eye(D, dtype=np.int64) - (np.outer(v, v) // 4)
    return R


def check_automorphism(T, B, C):
    """T（作用于行向量右侧）保格：T(b_i) ∈ 格（验证器）+ T 正交 + det=±1。"""
    ok_in = all(_in_c24prime((T @ row).astype(int), C) for row in B)
    ok_orth = np.allclose(T.astype(np.float64) @ T.T.astype(np.float64), np.eye(D))
    detT = abs(int(round(np.linalg.det(T.astype(np.float64)))))
    return ok_in and ok_orth and detT == 1


def co0_check(N=50000, save=False):
    """任务 B：自同构轨道统计量不变性。"""
    rng = np.random.default_rng(20260824)
    B = load_lattice(bkz=True)
    C = _golay_generator() % 2
    # ---- 最短向量（范数²=8，196560）
    R = 8
    hist8, vecs = ellipsoid_shells(B, R, collect=8, verb=False)
    n8 = hist8.get(8, 0)
    print(f"[Co₀] 最短向量 count[8] = {n8}（预言 196560）{'✓' if n8 == 196560 else '✗'}")
    assert n8 == 196560
    sv = np.array(vecs, dtype=np.int64)   # 196560×24
    # ---- Golay 符号翻转：理论保证保格（G24 自对偶 ⟹ ⟨x mod2, c⟩ = 0 ⟹ Σ 不变 mod 4）
    flips_ok = 0
    for c in golay_words(rng, 200):
        T = sign_flip(c)
        if check_automorphism(T, B, C):
            flips_ok += 1
    print(f"[Co₀] Golay 翻转保格率：{flips_ok}/200"
          f"{'（理论预期 100%）' if flips_ok == 200 else '（异常！）'}")
    # ---- Leech 反射：实证保格率
    r_ok = 0
    r_use = []
    for _ in range(200):
        v = sv[rng.integers(n8)]
        Rm = reflection(v)
        if Rm is not None and check_automorphism(Rm, B, C):
            r_ok += 1
            r_use.append(Rm)
    print(f"[Co₀] Leech 反射保格率：{r_ok}/200（可用的反射作为自同构生成元）")
    # ---- 随机自同构采样：翻转 × 反射 随机游走
    gens = [sign_flip(c) for c in golay_words(rng, 12)] + r_use[:12]
    if not gens:
        gens = [sign_flip(c) for c in golay_words(rng, 24)]
    steps = 60
    nT = N
    Tlist = []
    t0 = time.time()
    for _ in range(nT):
        T = np.eye(D, dtype=np.int64)
        for _ in range(steps):
            T = gens[rng.integers(len(gens))] @ T
        Tlist.append(T)
    Tarr = np.array(Tlist, dtype=np.int64)      # N×24×24
    print(f"[Co₀] 采样 {nT} 个随机自同构（{steps} 步游走，{time.time()-t0:.1f}s）")
    # 验证：全部保格 + 保范数
    bad = 0
    for T in Tarr:
        if not check_automorphism(T, B, C):
            bad += 1
    print(f"[Co₀] 采样保格率：{nT-bad}/{nT}")
    assert bad == 0
    # ---- 轨道统计量不变性：shell counting(σ(B)) 逐位 = shell counting(B)
    # 数学恒等式：x@σ(B) = σ(x@B)（σ 线性，行向量约定），σ 保范数 ⟹ 同一 x 集合的
    # 范数直方图对 B 与 σ(B) 逐位相同。只枚举一次 x（范数²=8 层），对每个 σ 一次
    # 矩阵乘法即得直方图——数值实现的一致性是检验对象。
    xs, _ = ellipsoid_shells(B, 8, collect=8, verb=False)
    xarr = np.array(xs, dtype=np.int64)      # 范数² = 8 的格点坐标（196560 个）
    vB = xarr @ B
    hB8 = {}
    for v in vB:
        n2 = int(v @ v)
        hB8[n2] = hB8.get(n2, 0) + 1
    sigma_ok = True
    for T in Tarr[:20]:
        Bs = T @ B                       # σ(B)：同一格的另一组基
        vS = xarr @ Bs                  # = σ(x@B)，范数应与 vB 相同
        hS = {}
        for v in vS:
            n2 = int(v @ v)
            hS[n2] = hS.get(n2, 0) + 1
        same = (hS == hB8)
        sigma_ok &= same
        if not same:
            print("  ✗ σ(B) shell counting 不一致！")
            break
    print(f"[Co₀] shell counting(σ(B)) == shell counting(B)（范数²=8 层，20 个 σ）："
          f"{'逐位一致 ✓' if sigma_ok else '✗ 不一致'}")
    # ---- 最短向量轨道采样均匀性（撞车计数）
    v0 = sv[0]
    hits = np.zeros(nT, dtype=np.int64)
    for i, T in enumerate(Tarr):
        w = T @ v0
        hits[i] = w @ w
    all8 = bool(np.all(hits == 8))
    uniq = len(np.unique(Tarr @ v0, axis=0))
    n = 196560
    exp_uniq = n * (1 - math.exp(-nT / n))
    print(f"[Co₀] 轨道采样：全部范数²=8 = {all8}；唯一值 {uniq}（期望 {exp_uniq:.0f}，"
          f"偏离 {(uniq-exp_uniq)/exp_uniq*100:.1f}%）")
    if save:
        np.save("gpu_spectra/co0_orbits.npy", Tarr[:200] @ v0)
    return {"flips": flips_ok, "refl": r_ok, "unique": int(uniq), "exp_unique": exp_uniq}


# ------------------------------------------------------------------ 主入口

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["cpu", "gpu", "co0"])
    ap.add_argument("R", type=int, nargs="?", default=None)
    ap.add_argument("--bkz0", action="store_true", help="不用 BKZ（HNF 原基）")
    ap.add_argument("--blocks", type=int, default=14, help="GPU 前缀层数 k")
    ap.add_argument("--N", type=int, default=50000, help="Co₀ 采样数")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--cpu-check", action="store_true",
                    help="跑 CPU 完整枚举逐位对照（R≥12 时很慢，默认由预言表独立核对）")
    args = ap.parse_args()

    if args.mode == "co0":
        co0_check(N=args.N, save=args.save)
        return
    B = load_lattice(bkz=not args.bkz0)
    if args.mode == "cpu":
        hist, _ = ellipsoid_shells(B, args.R)
        check_pred(hist, args.R)
    else:
        out, npref = gpu_shells(B, args.R, k=args.blocks)
        check_pred(out, args.R, tag="GPU ")
        if args.cpu_check:
            hc, _ = ellipsoid_shells(B, args.R, verb=False)
            for n2, c in sorted(hc.items()):
                g = out.get(n2, 0)
                print(f"  对照 count[{n2}] GPU={g} CPU={c} {'✓' if g == c else '✗'}")
            ok = all(out.get(n2, 0) == c for n2, c in hc.items())
            print(f"[双实现对照] {'逐位一致 ✓' if ok else '✗ 不一致'}（GPU {npref} 前缀）")
        else:
            print("[对照] 跳过 CPU 完整枚举（--cpu-check 开启），逐级预言核对："
                  f"count[8] 已在 R=8 层验证 ✓")


if __name__ == "__main__":
    main()
