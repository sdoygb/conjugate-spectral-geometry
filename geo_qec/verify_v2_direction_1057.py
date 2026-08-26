#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2 方向统计补充检验（10.57 §3.3 独立复现）：
最短向量方向 vs Gram 最小特征值特征方向的余弦平方 ρ = cos²θ/(1/n)。
文章 12 样本、ρ 散布 0.00–3.59、无系统性对齐。本文 20 样本独立验证。"""
import sys
sys.path.insert(0, "geo_qec")
import numpy as np
from verify_spectral_band_1057 import (mlkem_qary_basis, ntru_qary_basis,
                                       lll_reduce, gram_spectrum)

RNG = np.random.default_rng(20260822)

def rho_stats(B):
    """返回 (cos2, rho)：b1（LLL 最短向量）与 λ1 特征方向 u1 的对齐。"""
    Br = lll_reduce(B)
    G = Br.astype(np.float64) @ Br.astype(np.float64).T
    evals, evecs = np.linalg.eigh(G)  # 升序
    u1 = evecs[:, 0]
    b1 = Br[0].astype(np.float64)  # LLL 首行 ≈ 最短向量
    nb = np.linalg.norm(b1)
    if nb == 0:
        return None
    cos2 = float((u1 @ b1) ** 2 / (nb * nb))
    n = Br.shape[0]
    return cos2, cos2 * n

rows = []
# ML-KEM: d=16/32, 5 样本
for d in (16, 32):
    for s in range(5):
        B = mlkem_qary_basis(3329, d, 2, seed=3000 + s)
        r = rho_stats(B)
        if r:
            rows.append(("ML-KEM", d, s, *r))
# NTRU: d=16/32, 5 样本
for d in (16, 32):
    for s in range(5):
        B = ntru_qary_basis(2048, d, seed=4000 + s)
        r = rho_stats(B)
        if r:
            rows.append(("NTRU", d, s, *r))

print(f"{'格':<6}{'d':<5}{'样本':<5}{'cos²θ':<10}{'ρ=cos²θ·n':<12}")
all_rho = []
for fam, d, s, cos2, rho in rows:
    all_rho.append(rho)
    print(f"{fam:<6}{d:<5}{s:<5}{cos2:<10.4f}{rho:<12.3f}")

arr = np.array(all_rho)
print("-" * 50)
print(f"共 {len(arr)} 样本；ρ 范围 [{arr.min():.2f}, {arr.max():.2f}]；"
      f"均值 {arr.mean():.2f}；中位 {np.median(arr):.2f}")
print(f"ρ ≤ 1 的样本数: {(arr <= 1).sum()}/{len(arr)}（均匀期望 ρ=1）")
print(f"结论: {'无系统性方向对齐（与 10.57 §3.3 一致）' if arr.max() < 10 and (arr <= 3.6).all() else '需审视'}")

# 对照：随机方向（零假设）的 ρ 分布
n_rand = np.random.default_rng(1).normal(size=(10000, 64))
n_rand /= np.linalg.norm(n_rand, axis=1, keepdims=True)
cos2_rand = (n_rand[:, 0] ** 2).mean()
print(f"零假设（64 维随机方向）E[cos²θ] = 1/64 = {1/64:.4f}（实测 {cos2_rand:.4f}）")
