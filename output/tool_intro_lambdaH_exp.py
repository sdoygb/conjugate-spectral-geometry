# -*- coding: utf-8 -*-
"""工具引入实验 1（修复版）：LLL 后 Λ_H 波动的结构分解验证
对象：negacyclic 随机 A ∈ Z_q^{d×d}（中心化代表，满足定理 0.9.4.02 的实负循环前提），无调制 q-ary 格
"""
import numpy as np
import time

def negacyclic_from_row(a, q):
    """负循环矩阵（中心化代表）：A[j,k] = a[(k-j) mod d]·(-1)^{[k<j]}，条目取整数（-a 直接取负）"""
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

def lll_reduce(B, delta=0.75, max_iter=200000):
    B = np.array(B, dtype=np.float64).copy()
    m, n = B.shape
    mu = np.zeros((m, m))
    bstar = np.zeros((m, n))
    Bnorm = np.zeros(m)

    def update_gso():
        for i in range(m):
            bstar[i] = B[i].copy()
            for j in range(i):
                mu[i, j] = float(np.dot(B[i], bstar[j]) / Bnorm[j])
                bstar[i] -= mu[i, j] * bstar[j]
            Bnorm[i] = float(np.dot(bstar[i], bstar[i]))
            if Bnorm[i] < 1e-200:
                Bnorm[i] = 1e-200

    update_gso()
    k = 1
    it = 0
    while k < m:
        it += 1
        if it > max_iter:
            break
        for j in range(k - 1, -1, -1):
            if abs(mu[k, j]) > 0.5:
                qq = round(mu[k, j])
                B[k] -= qq * B[j]
                for jj in range(j + 1):
                    mu[k, jj] -= qq * mu[j, jj]
        bstar[k] = B[k].copy()
        for j in range(k):
            mu[k, j] = float(np.dot(B[k], bstar[j]) / Bnorm[j])
            bstar[k] -= mu[k, j] * bstar[j]
        Bnorm[k] = float(np.dot(bstar[k], bstar[k]))
        if Bnorm[k] < 1e-200:
            Bnorm[k] = 1e-200
        if Bnorm[k] >= (delta - mu[k, k - 1] ** 2) * Bnorm[k - 1]:
            k += 1
        else:
            B[[k, k - 1]] = B[[k - 1, k]]
            update_gso()
            k = max(k - 1, 1)
    return np.round(B).astype(np.int64), Bnorm, it

def lambdaH(G):
    ev = np.sort(np.linalg.eigvalsh(np.array(G, dtype=np.float64)))
    return ev[1] / ev[0]

def run(d, N, q=3329):
    out = []
    for trial in range(N):
        rng = np.random.default_rng(5000 + trial)
        a = rng.integers(0, q, size=d)
        A = negacyclic_from_row(a, q)
        B = np.zeros((2 * d, 2 * d), dtype=np.int64)
        B[:d, :d] = A
        B[:d, d:] = np.eye(d, dtype=np.int64)
        B[d:, d:] = q * np.eye(d, dtype=np.int64)
        LH0 = lambdaH(B @ B.T)
        t0 = time.time()
        Blll, Bnorm, it = lll_reduce(B)
        dt = time.time() - t0
        G1 = Blll @ Blll.T
        LH1 = lambdaH(G1)
        gso2 = Bnorm[1] / Bnorm[0] if Bnorm[0] > 0 else np.nan
        b1q = np.sqrt(Bnorm[0]) / q
        # LLL 第一行与 q 的比（λ1 = q 的验证）
        b1_len = np.linalg.norm(Blll[0])
        out.append((LH0, LH1, gso2, b1q, b1_len / q, dt, it))
    return np.array(out, dtype=float)

if __name__ == "__main__":
    for d, N in [(16, 40), (32, 20)]:
        R = run(d, N)
        LH0, LH1, gso2, b1q, b1_len_q = R[:, 0], R[:, 1], R[:, 2], R[:, 3], R[:, 4]
        print(f"=== d={d}, N={N} ===")
        print(f"原始 Λ_H:  min={LH0.min():.8f} max={LH0.max():.8f}（应=1，定理0.9.4.02）")
        print(f"LLL后 Λ_H: mean={LH1.mean():.3f} std={LH1.std():.3f} CV={LH1.std()/LH1.mean():.3f} "
              f"区间=[{LH1.min():.3f}, {LH1.max():.3f}]")
        print(f"经验对照(0.9): 均值 2.10, CV 0.37, 区间 [1.02, 3.55] (d=512,N=20)")
        ratio = LH1 / gso2
        print(f"分解检验: Λ_H/(||b*_2||/||b*_1||)^2: mean={ratio.mean():.3f} std={ratio.std():.3f}（应≈常数）")
        print(f"||b*_1||/q: mean={b1q.mean():.3f} std={b1q.std():.3f}；||b_1||/q: mean={b1_len_q.mean():.3f}（λ1=q 代理, 应≈1）")
        print(f"相关 Λ_H vs GSO比²: r={np.corrcoef(LH1, gso2)[0,1]:.3f}")
        print(f"LLL 耗时: mean={R[:,5].mean():.3f}s, 迭代: mean={R[:,6].mean():.0f}")
        print()
