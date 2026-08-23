#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# diag_spectrum.py — A-A 块谱分析：Gram 恒等式、SVD 谱、三角核近似链
# 验证: G = M_AA·diag(σ_A)·M_AAᵀ ≈ Gram(B_AA);  λ_max(MMᵀ) ↔ λ_max(G)/σ_eff ↔ λ_max(T̂)/σ_eff
# 用法: python3 diag_spectrum.py [d] [mode] [seed] [sh]
import numpy as np, json, sys, time
from fpylll import IntegerMatrix, LLL

Q = 3329

def build_A(row, mode):
    d = len(row)
    A = np.zeros((d, d), dtype=np.int64)
    for i in range(d):
        for k in range(d):
            v = int(row[(k - i) % d])
            if k < i:
                v = -v
            A[i, k] = v
    if mode == 'cent':
        A[A > Q // 2] -= Q
        A[A < -Q // 2] += Q
    elif mode == 'mod':
        A = np.mod(A, Q)
    return A

def build_B0(row, mode):
    d = len(row)
    A = build_A(row, mode)
    B0 = np.zeros((2 * d, 2 * d), dtype=np.int64)
    B0[:d, :d] = A
    B0[:d, d:] = np.eye(d, dtype=np.int64)
    B0[d:, d:] = Q * np.eye(d, dtype=np.int64)
    return B0

def gso_mu(B):
    n = B.shape[0]
    Bf = B.astype(np.float64)
    mu = np.zeros((n, n))
    sig = np.zeros(n)
    bs = np.zeros((n, n))
    for i in range(n):
        v = Bf[i].copy()
        for j in range(i):
            m = np.dot(v, bs[j]) / sig[j]
            mu[i, j] = m
            v = v - m * bs[j]
        sig[i] = np.dot(v, v)
        bs[i] = v
        mu[i, i] = 1.0   # 单位下三角口径（对角=1）
    return sig, mu, bs

def lll_with_U(B0):
    n = B0.shape[0]
    M = IntegerMatrix(n, n)
    U = IntegerMatrix(n, n)
    for i in range(n):
        U[i, i] = 1
        for j in range(n):
            M[i, j] = int(B0[i, j])
    LLL.reduction(M, U)
    B = np.array([[M[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    Ua = np.array([[U[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    return B, Ua

def kendall_tau(a, b):
    # 平均秩 Kendall tau（处理重复）
    n = len(a)
    def rankdata(x):
        order = np.argsort(x, kind='stable')
        ranks = np.empty(n, dtype=float)
        i = 0
        while i < n:
            j = i
            while j + 1 < n and x[order[j + 1]] == x[order[i]]:
                j += 1
            ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
            i = j + 1
        return ranks
    ra, rb = rankdata(np.array(a)), rankdata(np.array(b))
    # tau = corr of ranks (Pearson on ranks = Kendall 近似); 用精确逆序数更快路径:
    order = np.argsort(rb, kind='stable')
    seq = ra[order]
    inv = 0
    for i in range(n):
        for j in range(i + 1, n):
            if seq[i] > seq[j]:
                inv += 1
    return 1 - 4 * inv / (n * (n - 1))

def run(seed, mode, shuffle, d):
    rng = np.random.default_rng(seed)
    row = rng.integers(0, Q, d)
    B0 = build_B0(row, mode)
    if shuffle:
        perm = rng.permutation(d)
        B0[:d] = B0[perm]      # A 块行重排（每行内容不变）
    n = 2 * d
    B, U = lll_with_U(B0)
    ok = np.array_equal(U @ B0, B)
    sig, mu, bs = gso_mu(B)
    kmain = np.argmax(np.abs(U), axis=1)
    tmain = (kmain >= d)
    apos = np.where(~tmain)[0]
    # A-A 块（输出序）
    muAA = mu[np.ix_(apos, apos)]
    sigA = sig[apos]
    BAA = B[apos, :]
    # 1) Gram 恒等式: G = M_AA·S·M_AAᵀ vs Gram(B_AA)
    G1 = muAA @ np.diag(sigA) @ muAA.T
    G2 = BAA @ BAA.T
    gdiff = np.max(np.abs(G1 - G2)) / max(1.0, np.max(np.abs(G2)))
    # 2) 谱量
    Mfull = mu
    lam_full = np.linalg.eigvalsh(Mfull @ Mfull.T)[-1]
    lam_AA = np.linalg.eigvalsh(muAA @ muAA.T)[-1]
    lam_G = np.linalg.eigvalsh(G1)[-1]
    # σ 权重: σ_eff = Σσ_j·‖M_{·,j}‖²/Σ‖M_{·,j}‖² (trace 加权)
    colE = np.sum(muAA**2, axis=0) + 1.0
    sig_eff = np.sum(sigA * colE) / np.sum(colE)
    lam_G_over = lam_G / sig_eff
    # 3) SVD 谱（A-A 块）
    Uu, S, Vt = np.linalg.svd(muAA)
    S2 = S**2
    tot = S2.sum()
    s1 = S2[0] / tot
    s2 = S2[1] / tot if len(S2) > 1 else 0.0
    s3 = S2[2] / tot if len(S2) > 2 else 0.0
    rank1 = np.outer(Uu[:, 0] * S[0], Vt[0, :])
    r1res = np.linalg.norm(muAA - rank1) / np.linalg.norm(muAA)
    # 4) 输入行差分箱的 Gram 核 K(Δ) → Toeplitz T̂
    dmax = d
    Kbar_in = np.zeros(dmax)
    cnt_in = np.zeros(dmax)
    ki = kmain[apos]
    for i in range(d):
        for j in range(i):
            dd = abs(ki[i] - ki[j])
            Kbar_in[dd] += G2[i, j]
            cnt_in[dd] += 1
    for dd in range(dmax):
        if cnt_in[dd] > 0:
            Kbar_in[dd] /= cnt_in[dd]
    T = np.zeros((d, d))
    for i in range(d):
        for j in range(d):
            T[i, j] = Kbar_in[abs(i - j)]
    lam_T = np.linalg.eigvalsh(T)[-1]
    f0 = Kbar_in.sum()
    # 输入序 Toeplitz（正确方向：λ_max 与置换无关）
    Tt = np.zeros((d, d))
    for k1 in range(d):
        for k2 in range(d):
            Tt[k1, k2] = Kbar_in[abs(k1 - k2)]
    lam_Tt = np.linalg.eigvalsh(Tt)[-1]
    f0t = Kbar_in.sum()
    lam_G_ratio_Tt = lam_G / lam_Tt
    f0t_ratio = f0t / lam_Tt
    # 理论核 K(Δ) ~ (d q²/12)(1-Δ/d)³（三角核, §3.1 形状）; f0_theory = Σ K(Δ)
    x = np.arange(d) / d
    Ktheory = (d * Q**2 / 12.0) * (1 - x)**3
    f0_theory = Ktheory.sum()
    lam_Tt_theory = f0_theory  # 正核主项
    lam_G_ratio_theory = lam_G / lam_Tt_theory
    kmin = Kbar_in.min()
    # 5) 列相关性（按 |j-j'| 分箱, 8 箱）
    corr_bins = {}
    muN = muAA / (np.linalg.norm(muAA, axis=0) + 1e-12)
    for j1 in range(d):
        for j2 in range(j1 + 1, d):
            dd = abs(j1 - j2) // max(1, d // 8)
            lo = max(j1, j2)
            c = np.dot(muN[lo:, j1], muN[lo:, j2])
            corr_bins.setdefault(dd, []).append(c)
    corr_means = {k: float(np.mean(v)) for k, v in sorted(corr_bins.items())}
    # 6) 每列能量
    col_energy = np.sum(muAA**2, axis=0)
    # 7) 比值
    ratio = lam_full / lam_G_over
    tau = kendall_tau(list(range(d)), list(ki))
    res = {
        'seed': seed, 'mode': mode, 'shuffle': shuffle, 'd': d, 'u_ok': bool(ok),
        'gdiff': float(gdiff), 'lam_full': float(lam_full), 'lam_AA': float(lam_AA),
        'lam_G': float(lam_G), 'sig_eff': float(sig_eff), 'lam_G_over': float(lam_G_over),
        'ratio': float(ratio), 's1': float(s1), 's2': float(s2), 's3': float(s3),
        'r1res': float(r1res), 'lam_T': float(lam_T), 'f0': float(f0),
        'lam_T_over': float(lam_T / sig_eff),
        'lam_Tt': float(lam_Tt), 'lam_Tt_over': float(lam_Tt / sig_eff),
        'lam_G_ratio_Tt': float(lam_G_ratio_Tt), 'f0t_ratio': float(f0t_ratio),
        'f0_theory': float(f0_theory), 'lam_G_ratio_theory': float(lam_G_ratio_theory),
        'kmin': float(kmin), 'corr': corr_means,
        'colE_mean': float(col_energy.mean()), 'colE_max': float(col_energy.max()),
        'tau': float(tau),
    }
    return res

if __name__ == '__main__':
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    mode = sys.argv[2] if len(sys.argv) > 2 else 'real'
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    shuffle = len(sys.argv) > 4 and sys.argv[4] == 'sh'
    t0 = time.time()
    r = run(seed, mode, shuffle, d)
    print(json.dumps(r))
    print('# time %.1fs' % (time.time() - t0), file=sys.stderr)
