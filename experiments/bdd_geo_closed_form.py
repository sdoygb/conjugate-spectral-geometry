#!/usr/bin/env python3
"""方向A实验：Voronoi 几何闭式（一阶墙近似）vs 模拟 BDD 解码失败率
q-ary 格 Λ = {(y,z) ∈ Z^32 : z ≡ Ay mod q}，A = negacyclic(n=16)
BDD 目标 t = (0, b), b = As+e mod q；最近格点 x 分量 = s 即成功
闭式：fail_wall = 2·P(⟨(s,e), v1⟩ ≥ ‖v1‖²/2)，v1 = 最短向量（±两墙）
"""
import numpy as np, fpylll, time, sys

def negacyclic_A(n, q, rng):
    a = rng.integers(0, q, size=n)
    A = np.zeros((n, n), dtype=np.int64)
    for i in range(n):
        for j in range(n):
            k = (j - i) % n
            A[i, j] = a[k] * (-1 if j < i else 1)
    return A

def qary_basis(A, q):
    n = A.shape[0]
    N = 2*n
    B = np.zeros((N, N), dtype=np.int64)
    B[:n, :n] = q*np.eye(n, dtype=np.int64)
    B[n:, :n] = A
    B[n:, n:] = np.eye(n, dtype=np.int64)
    return B

def cbd_sample(rng, n, eta):
    return rng.integers(-1, 2, size=(2*eta, n)).sum(axis=0)

def cbd_pdf(eta):
    d = np.array([1/3, 1/3, 1/3])
    for _ in range(2*eta - 1):
        d = np.convolve(d, [1/3, 1/3, 1/3])
    return d  # d[k] = P(X = k - 2*eta)

def wall_prob(v, n, eta):
    """P(⟨v, x⟩ >= ceil(‖v‖²/2))，x ∈ Z^(2n)，系数 iid CBD_eta —— 精确卷积"""
    v = np.asarray(v, dtype=np.int64)
    d = cbd_pdf(eta)
    off = 2*eta
    R = 2*eta*int(np.abs(v).sum())
    pdf = np.zeros(2*R+1); pdf[R] = 1.0
    for i in range(2*n):
        vi = int(v[i])
        if vi == 0: continue
        new = np.zeros(2*R+1)
        for t in range(-R, R+1):
            p = pdf[t+R]
            if p == 0: continue
            for k in range(len(d)):
                val = vi*(k - off)
                if abs(t+val) <= R:
                    new[t+val+R] += p*d[k]
        pdf = new
    T = (int(v @ v) + 1)//2   # ceil(‖v‖²/2)
    return pdf[T+R:].sum()

def babai_nearest(B, t):
    """最近平面法（LLL/BKZ 约化基上）"""
    n = B.shape[0]
    Bf = B.astype(np.float64)
    Bn = Bf.copy()
    for i in range(n):
        for j in range(i):
            Bn[i] -= np.dot(Bn[i], Bn[j]) / np.dot(Bn[j], Bn[j]) * Bn[j]
    tc = t.astype(np.float64).copy()
    coeff = np.zeros(n, dtype=np.float64)
    for i in range(n-1, -1, -1):
        c = round(np.dot(tc, Bn[i]) / np.dot(Bn[i], Bn[i]))
        tc -= c*Bf[i]
        coeff[i] = c
    return coeff.round().astype(np.int64)

def run_instance(q, eta, seed, N=20000):
    n = 16
    rng = np.random.default_rng(1000*seed + q)
    A = negacyclic_A(n, q, rng)
    B = qary_basis(A, q)
    M = fpylll.IntegerMatrix.from_matrix(B.tolist())
    fpylll.LLL.reduction(M)
    fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=25, max_loops=4))
    Bf = np.array([[M[i][j] for j in range(2*n)] for i in range(2*n)], dtype=np.int64)
    v1 = Bf[0]                      # BKZ 第一向量 = λ₁ 上界近似
    l1 = float(np.linalg.norm(v1))
    gh = np.sqrt(32/(2*np.pi*np.e))*np.sqrt(q)
    fw = 2*wall_prob(v1, n, eta)    # 一阶墙闭式（±v1 两墙）
    fails = 0
    for _ in range(N):
        s = cbd_sample(rng, n, eta)
        e = cbd_sample(rng, n, eta)
        b = (A @ s + e) % q
        b = b - q*(b > q//2)        # 提升到 (-q/2, q/2]
        t = np.zeros(2*n, dtype=np.int64); t[n:] = b
        coeff = babai_nearest(Bf, t)
        v = (coeff[:, None]*Bf).sum(axis=0)
        if not np.array_equal(v[:n], s):
            fails += 1
    return l1, gh, fw, fails/N

if __name__ == "__main__":
    t0 = time.time()
    for (q, eta, label) in [(61, 2, 'q=61  eta=2'), (97, 3, 'q=97  eta=3')]:
        for seed in range(3):
            l1, gh, fw, fs = run_instance(q, eta, seed)
            print(f"{label} seed={seed}: λ1≤{l1:6.2f}  GH={gh:6.2f}  "
                  f"fail_wall={fw:8.5f}  fail_sim={fs:8.5f}  ratio={fs/fw:6.2f}", flush=True)
    print(f"[done] {time.time()-t0:.1f}s")
