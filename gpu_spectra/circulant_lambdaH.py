#!/usr/bin/env python3
"""circulant_lambdaH.py — 群尺度刚性机制检验：保 G 的循环对称 vs 高对称格
假设（10.75 精确化，2026-08-23）：
  群尺度零方差的判据不是 |Aut| 大小，而是对称群是否保 Gram 矩阵 G（表示论 Schur 引理）。
  negacyclic（Z_{2d}，0.9 已验证 Λ_H≡1）与 circulant（Z_d）都保 G（傅里叶基分块对角），
  预测：随机系数系综下 std(Λ_H) → 0（零方差）。
  对照：E8/Leech 自同构（Co₀, W(E8)）是整数矩阵、不保规范基 G → 无零方差（已测得 std~1.5-2.3）。

结构（与 0.9 §4 相同）：
  A = circulant(a), a ∈ Z_q^d；G = [[AAᵀ + I, qI], [qI, q²I]]（2d×2d）
  傅里叶基下 G 分块对角，块 B_k = [[|â_k|²+1, q],[q,q²]]，k ↔ -k 成对 ⟹ λ₁ 重数 2
  预测：Λ_H ≡ 1 对全部样本（除非 k=0 块单独给出 λ₁，均值仍确定、std=0）。
"""
import sys
sys.path.insert(0, "gpu_spectra")
import numpy as np
from lambda_H import gen_G_numpy

Q = 3329

def circulant_G_numpy(d, q, N, seed=20260823):
    """circulant 系综：a 随机 → A = circulant(a) → G（与 negacyclic 同构型）
    返回 (N, 2d, 2d)"""
    rng = np.random.default_rng(seed)
    Gs = np.empty((N, 2 * d, 2 * d))
    for t in range(N):
        a = rng.integers(0, q, d).astype(np.float64)
        idx = (np.arange(d)[:, None] - np.arange(d)[None, :]) % d
        A = a[idx]
        AA = A @ A.T
        G = np.empty((2 * d, 2 * d))
        G[:d, :d] = AA + np.eye(d)
        G[:d, d:] = np.eye(d) * q
        G[d:, :d] = np.eye(d) * q
        G[d:, d:] = np.eye(d) * q * q
        Gs[t] = G
    return Gs

def run(d, N=512):
    Gs = circulant_G_numpy(d, Q, N)
    eg = np.sort(np.linalg.eigvalsh(Gs), axis=1)
    lam = eg[:, 1] / eg[:, 0]
    print(f"[circulant Z_{d}] N={N}  mean(Λ_H)={lam.mean():.10f}  "
          f"std={lam.std():.3e}  max|Λ_H−1|={np.max(np.abs(lam-1)):.3e}  "
          f"min={lam.min():.10f}  max={lam.max():.10f}")
    return lam

def run_negacyclic(d, N=512):
    """对照：negacyclic（0.9 已验证，重跑确认同构型可比）"""
    Gs = gen_G_numpy(d, Q, N, mode=0, seed=20260823)
    eg = np.sort(np.linalg.eigvalsh(Gs), axis=1)
    lam = eg[:, 1] / eg[:, 0]
    print(f"[negacyclic Z_2d] d={d} N={N}  mean(Λ_H)={lam.mean():.10f}  "
          f"std={lam.std():.3e}  max|Λ_H−1|={np.max(np.abs(lam-1)):.3e}")
    return lam

if __name__ == "__main__":
    print("=" * 92)
    print("群尺度刚性机制检验：保 G 对称（circulant Z_d）vs 不保 G（E8/Leech 自同构）")
    print("=" * 92)
    for d in (8, 16, 32):
        run(d)
    print("-" * 92)
    for d in (8, 16, 32):
        run_negacyclic(d)
    print("-" * 92)
    print("对照（highsym_spectra 系综，充分混合 nsteps=400，LLL 后）：")
    print("  E8   : std ≈ 1.6-1.8   Leech: std ≈ 1.8-2.3   随机24: std ≈ 1.2-1.6")
