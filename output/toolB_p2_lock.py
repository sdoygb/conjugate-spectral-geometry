import numpy as np, time, sys
from fpylll import IntegerMatrix, LLL

Q = 3329
def negacyclic_from_row(row, q):
    d = len(row); A = np.zeros((d, d), dtype=np.int64)
    for i in range(d):
        for j in range(d):
            k = (j - i) % d
            A[i, j] = row[k] if j >= i else (-row[k]) % q
    return A

def gso_mu(B):
    n = B.shape[0]; Bf = B.astype(np.float64)
    bstar = np.zeros_like(Bf); mu = np.zeros((n, n)); sigma = np.zeros(n)
    for i in range(n):
        if i == 0:
            bstar[0] = Bf[0].copy(); sigma[0] = np.dot(Bf[0], Bf[0]); mu[0,0] = 1.0; continue
        num = Bf[i] @ bstar[:i].T
        mu[i, :i] = num / sigma[:i]
        bstar[i] = Bf[i] - mu[i, :i] @ bstar[:i]
        sigma[i] = np.dot(bstar[i], bstar[i])
    np.fill_diagonal(mu, 1.0)
    return sigma, mu

d, N, delta = 256, 20, 0.75
res = []
for s in range(N):
    rng = np.random.default_rng(s)
    a = rng.integers(0, Q, size=d)
    A = negacyclic_from_row(a, Q)
    B0 = np.zeros((2*d, 2*d), dtype=np.int64)
    B0[:d, :d] = A; B0[:d, d:] = np.eye(d, dtype=np.int64)
    B0[d:, d:] = Q * np.eye(d, dtype=np.int64)
    # 原始谱
    G0 = B0 @ B0.T
    ev0 = np.linalg.eigvalsh(G0.astype(np.float64))
    LH0 = ev0[1]/ev0[0]
    # LLL
    M = IntegerMatrix.from_matrix(B0.tolist())
    LLL.reduction(M, delta=delta)
    Blll = np.array([[M[i,j] for j in range(M.ncols)] for i in range(M.nrows)])
    G = Blll @ Blll.T
    ev = np.linalg.eigvalsh(G.astype(np.float64))
    LH = ev[1]/ev[0]
    sigma, mu = gso_mu(Blll)
    MM = mu @ mu.T
    evm = np.linalg.eigvalsh(MM)
    kappa = evm[1]/evm[0]
    res.append((s, LH0, LH, kappa))
    print(f"seed {s}: LH0={LH0:.6f} LH={LH:.4f} kappa={kappa:.4f}", flush=True)

res = np.array(res)
np.save("output/toolB_p2_lock.npz", res)
LH = res[:,2]; kappa = res[:,3]
print(f"\nDONE d={d} delta={delta} N={N}")
print(f"LLL后 Λ_H: mean={LH.mean():.3f} std={LH.std():.3f} CV={LH.std()/LH.mean():.3f} [{LH.min():.3f}, {LH.max():.3f}]")
print(f"κ(μ): mean={kappa.mean():.3f} CV={kappa.std()/kappa.mean():.3f} [{kappa.min():.3f}, {kappa.max():.3f}]")
print(f"θ=Λ_H/κ: mean={(LH/kappa).mean():.3f}")
print(f"P(Λ_H>3.55)={np.mean(LH>3.55):.3f} P(Λ_H<1.02)={np.mean(LH<1.02):.3f}")
