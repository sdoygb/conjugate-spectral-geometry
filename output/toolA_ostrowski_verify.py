#!/usr/bin/env python3
"""工具 A 验证：Λ_H(G_LLL) = (θ₂/θ₁)·κ(μ) 分解
Ostrowski: λ_k(M^T diag(σ) M) = θ_k · λ_k(M M^T), θ_k ∈ [σ_min, σ_max]
"""
import numpy as np
from fractions import Fraction

np.random.seed(42)
Q = 3329

def negacyclic_from_row(a, q=Q):
    """中心化代表的负循环矩阵（实负循环，定理 0.9.4.02 适用）"""
    d = len(a)
    A = np.zeros((d, d), dtype=np.int64)
    for j in range(d):
        for k in range(d):
            s = (k - j) % d
            val = int(a[s])
            if k < j:
                val = -val
            A[j, k] = val
    return A

def lll(B0, delta=0.75, max_iter=200000):
    """LLL 归约（浮点），返回 (B, mu, sigma)，mu 为系数矩阵，sigma 为 GSO 长度平方"""
    B = B0.copy().astype(float)
    n = B.shape[0]
    mu = np.zeros((n, n))
    Bnorm = np.zeros(n)
    bstar = np.zeros_like(B)
    def update_gso():
        for i in range(n):
            bstar[i] = B[i].copy()
            for j in range(i):
                mu[i, j] = np.dot(B[i], bstar[j]) / Bnorm[j]
                bstar[i] -= mu[i, j] * bstar[j]
            Bnorm[i] = np.dot(bstar[i], bstar[i])
            if Bnorm[i] <= 1e-300:
                Bnorm[i] = 1e-300
    update_gso()
    it = 0
    k = 1
    while k < n and it < max_iter:
        it += 1
        # 大小归约
        for j in range(k - 1, -1, -1):
            qq = round(mu[k, j])
            if qq != 0:
                B[k] -= qq * B[j]
                for jj in range(j + 1):
                    mu[k, jj] -= qq * mu[j, jj]
                bstar[k] = B[k].copy()
                for jj in range(k):
                    bstar[k] -= mu[k, jj] * bstar[jj]
                Bnorm[k] = np.dot(bstar[k], bstar[k])
                if Bnorm[k] <= 1e-300:
                    Bnorm[k] = 1e-300
        # Lovász 交换
        if Bnorm[k] >= (delta - mu[k, k-1]**2) * Bnorm[k-1]:
            k += 1
        else:
            B[[k-1, k]] = B[[k, k-1]]
            update_gso()
            k = max(k - 1, 1)
    return B.astype(np.int64), mu, Bnorm

def run(d, N):
    rows = []
    for t in range(N):
        a = np.random.randint(0, Q, d)
        A = negacyclic_from_row(a)
        B0 = np.zeros((2*d, 2*d), dtype=np.int64)
        B0[:d, :d] = A
        B0[:d, d:] = np.eye(d, dtype=np.int64)
        B0[d:, d:] = Q * np.eye(d, dtype=np.int64)
        # 原始谱
        G0 = B0 @ B0.T
        lam0 = np.linalg.eigvalsh(G0.astype(float))
        LH0 = lam0[1] / lam0[0]
        # LLL
        Blll, mu, sigma = lll(B0)
        G = Blll @ Blll.T
        lam = np.linalg.eigvalsh(G.astype(float))
        LH = lam[1] / lam[0]
        # Ostrowski 验证
        M = np.tril(mu) + np.eye(2*d) - np.diag(np.diag(np.tril(mu)))
        M = np.tril(mu, -1) + np.eye(2*d)
        lmm = np.linalg.eigvalsh(M @ M.T)
        kappa = lmm[1] / lmm[0]
        theta1 = lam[0] / lmm[0]
        theta2 = lam[1] / lmm[1]
        s_min, s_max = sigma.min(), sigma.max()
        rows.append(dict(t=t, LH0=LH0, LH=LH, kappa=kappa,
                         theta1=theta1, theta2=theta2,
                         ratio=(theta2/theta1)*kappa,
                         s_min=s_min, s_max=s_max,
                         s_span=s_max/s_min,
                         l1G=lam[0], s1=sigma[0],
                         lam1MM=lmm[0], lam2MM=lmm[1]))
    return rows

for d, N in [(16, 40), (32, 15)]:
    rows = run(d, N)
    LH = np.array([r['LH'] for r in rows])
    kappa = np.array([r['kappa'] for r in rows])
    ratio = np.array([r['ratio'] for r in rows])
    span = np.array([r['s_span'] for r in rows])
    ok_theta = np.all([r['theta1'] >= r['s_min']/r['lam1MM']*0 and r['theta1'] <= r['s_max'] + 1e-6 and r['theta1'] >= r['s_min'] - 1e-6 for r in rows])
    print(f"=== d={d}, N={N} ===")
    print(f"原始 Λ_H: mean={LH0:.6f} (应=1)")
    print(f"LLL后 Λ_H: mean={LH.mean():.3f}, CV={LH.std()/LH.mean():.3f}, min={LH.min():.3f}, max={LH.max():.3f}")
    print(f"κ(μ)=λ₂(MMᵀ)/λ₁(MMᵀ): mean={kappa.mean():.3f}, CV={kappa.std()/kappa.mean():.3f}")
    print(f"(θ₂/θ₁)·κ(μ): mean={ratio.mean():.3f}, CV={ratio.std()/ratio.mean():.3f}")
    print(f"分解误差 |Λ_H - (θ₂/θ₁)κ|/Λ_H: mean={np.mean(np.abs(LH-ratio)/LH):.3f}")
    print(f"σ 跨度 σ_max/σ_min: mean={span.mean():.2f}, max={span.max():.2f}")
    print(f"θ₁ ∈ [σ_min,σ_max] 检查: {np.all([r['s_min']-1e-6 <= r['theta1'] <= r['s_max']+1e-6 for r in rows])}")
    print(f"θ₂ ∈ [σ_min,σ_max] 检查: {np.all([r['s_min']-1e-6 <= r['theta2'] <= r['s_max']+1e-6 for r in rows])}")
    corr = np.corrcoef(LH, kappa)[0,1]
    corr2 = np.corrcoef(LH, ratio)[0,1]
    print(f"corr(Λ_H, κ(μ)) = {corr:.3f}, corr(Λ_H, (θ₂/θ₁)κ) = {corr2:.3f}")
    print()
