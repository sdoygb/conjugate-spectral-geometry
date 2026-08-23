"""P2 复现尝试 v2：a ∈ [0,q-1] + 实数负循环（不取模）——实负循环定理 0.9.4.02 的签名对象。
对照：取模版（全非负条目）。delta = 0.99 / 0.75。
"""
import numpy as np, sys, time
from fpylll import IntegerMatrix, LLL

Q = 3329
d = 256
N = 20

def negacyclic_real(row, q):
    """实负循环：k>=j 取 a[(k-j)%d]，k<j 取 -a[(k-j)%d]（实数负号，不取模）"""
    d0 = len(row)
    A = np.zeros((d0, d0), dtype=np.int64)
    for i in range(d0):
        for j in range(d0):
            v = row[(j - i) % d0]
            A[i, j] = v if j >= i else -v
    return A

def negacyclic_mod(row, q):
    """取模负循环：-a mod q（条目全非负 [0,q-1]）"""
    d0 = len(row)
    A = np.zeros((d0, d0), dtype=np.int64)
    for i in range(d0):
        for j in range(d0):
            v = row[(j - i) % d0]
            A[i, j] = v % q if j >= i else (-v) % q
    return A

def gso_mu(B):
    n = B.shape[0]
    Bf = B.astype(np.float64)
    bstar = np.zeros_like(Bf)
    mu = np.zeros((n, n))
    sigma = np.zeros(n)
    for i in range(n):
        if i == 0:
            bstar[0] = Bf[0].copy()
            sigma[0] = np.dot(Bf[0], Bf[0])
            continue
        num = Bf[i] @ bstar[:i].T
        mu[i, :i] = num / sigma[:i]
        bstar[i] = Bf[i] - mu[i, :i] @ bstar[:i]
        sigma[i] = np.dot(bstar[i], bstar[i])
    np.fill_diagonal(mu, 1.0)
    return sigma, mu

def run_case(mode, delta):
    LHs, kaps, LH0s = [], [], []
    for seed in range(N):
        rng = np.random.default_rng(seed)
        a = rng.integers(0, Q, d)
        A = negacyclic_real(a, Q) if mode == "real" else negacyclic_mod(a, Q)
        B0 = np.zeros((2*d, 2*d), dtype=np.int64)
        B0[:d, :d] = A
        B0[:d, d:] = np.eye(d, dtype=np.int64)
        B0[d:, d:] = Q * np.eye(d, dtype=np.int64)
        G0 = B0.astype(np.float64) @ B0.astype(np.float64).T
        ev0 = np.linalg.eigvalsh(G0)
        LH0 = ev0[1] / ev0[0]
        M = IntegerMatrix.from_matrix(B0.tolist())
        LLL.reduction(M, delta=delta)
        B = np.array([[M[i, j] for j in range(M.ncols)] for i in range(M.nrows)])
        G = B.astype(np.float64) @ B.astype(np.float64).T
        ev = np.linalg.eigvalsh(G)
        LH = ev[1] / ev[0]
        sig, mu = gso_mu(B)
        MM = mu @ mu.T
        evm = np.linalg.eigvalsh(MM)
        kap = evm[1] / evm[0]
        LHs.append(LH); kaps.append(kap); LH0s.append(LH0)
    LHs = np.array(LHs); kaps = np.array(kaps); LH0s = np.array(LH0s)
    return LH0s, LHs, kaps

for mode in ["real", "mod"]:
    for delta in [0.99, 0.75]:
        t0 = time.time()
        LH0s, LHs, kaps = run_case(mode, delta)
        print(f"[{mode} delta={delta}] 原始Λ_H mean={LH0s.mean():.4f} std={LH0s.std():.2e}; "
              f"LLL后 Λ_H mean={LHs.mean():.3f} CV={LHs.std()/LHs.mean():.3f} "
              f"[{LHs.min():.2f},{LHs.max():.2f}]; κ mean={kaps.mean():.3f} "
              f"({time.time()-t0:.0f}s)", flush=True)
print("ALL DONE", flush=True)
