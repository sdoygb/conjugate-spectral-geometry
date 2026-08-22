#!/usr/bin/env python3
"""verify_mechanism.py — 零方差机制验证：Λ_H≠1 ⟺ 最小特征值块为自配对块
circulant: 块 B_k = [[|â_k|²+1, q],[q,q²]], k=0..d-1, k 与 d-k 配对；k=0, d/2 自配对。
negacyclic: 奇数频率块 B_j, j=0..d-1, j 与 d-1-j 配对，无自配对（d 偶数）。
预测：circulant 中 Λ_H≠1 的样本 ⟺ argmin_k |â_k|² ∈ {0, d/2}。
"""
import numpy as np

Q = 3329

def circulant_pairs(d, N=2000, seed=1):
    rng = np.random.default_rng(seed)
    hit_self, hit_pair = 0, 0
    lam_is_1 = 0
    for t in range(N):
        a = rng.integers(0, Q, d).astype(np.complex128)
        ak = np.fft.fft(a)                      # 傅里叶特征值 â_k
        m2 = np.abs(ak) ** 2
        kmin = int(np.argmin(m2))
        self_pair = (kmin == 0 or (d % 2 == 0 and kmin == d // 2))
        # 计算该样本 Λ_H
        G = np.empty((2 * d, 2 * d))
        idx = (np.arange(d)[:, None] - np.arange(d)[None, :]) % d
        A = a.real[idx]
        AA = A @ A.T
        G[:d, :d] = AA + np.eye(d)
        G[:d, d:] = np.eye(d) * Q
        G[d:, :d] = np.eye(d) * Q
        G[d:, d:] = np.eye(d) * Q * Q
        eg = np.sort(np.linalg.eigvalsh(G))
        lam = eg[1] / eg[0]
        if self_pair:
            hit_self += 1
            if abs(lam - 1) > 1e-6:
                print(f"  反例: kmin={kmin} 自配对但 Λ_H={lam:.6f} ≠ 1")
        else:
            hit_pair += 1
            if abs(lam - 1) > 1e-6:
                print(f"  反例: kmin={kmin} 配对但 Λ_H={lam:.6f} ≠ 1")
        if abs(lam - 1) < 1e-6:
            lam_is_1 += 1
    print(f"[circulant d={d}] N={N}: min块自配对 {hit_self} ({hit_self/N:.1%}), "
          f"配对 {hit_pair} ({hit_pair/N:.1%})；Λ_H=1 的样本 {lam_is_1} ({lam_is_1/N:.1%})")

if __name__ == "__main__":
    for d in (8, 16, 32):
        circulant_pairs(d)
