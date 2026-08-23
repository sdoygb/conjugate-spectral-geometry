"""10.58 P2 复现：中心化（实负循环）输入 vs 非中心化（[0,q-1]）输入，d=256, seed 0-19
检验：原始 Λ_H（应≡1 对中心化）、LLL 后 Λ_H（P2 经验 2.10 [1.02,3.55]）、κ、θ
"""
import numpy as np
from fpylll import IntegerMatrix, LLL

Q = 3329

def negacyclic_real(a, q, centered):
    """实负循环矩阵。centered=True: 系数在 [-q//2, q//2]（实负循环，不取模）
    centered=False: [0,q-1] 代表（模 q 负循环）"""
    d = len(a)
    A = np.zeros((d, d), dtype=np.int64)
    for j in range(d):
        for k in range(d):
            s = (k - j) % d
            val = int(a[s])
            if centered:
                if k < j:
                    val = -val
            else:
                if k < j:
                    val = (-val) % q
            A[j, k] = val
    return A

def build_B(A, q):
    d = A.shape[0]
    B = np.zeros((2*d, 2*d), dtype=np.int64)
    B[:d, :d] = A
    B[:d, d:] = np.eye(d, dtype=np.int64)
    B[d:, d:] = q * np.eye(d, dtype=np.int64)
    return B

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

d = 256
for centered in [True, False]:
    LHs, kaps, LH0s = [], [], []
    for seed in range(20):
        rng = np.random.default_rng(seed)
        if centered:
            a = rng.integers(-Q // 2, Q // 2 + 1, size=d)  # 中心化系数
        else:
            a = rng.integers(0, Q, size=d)
        A = negacyclic_real(a, Q, centered)
        B0 = build_B(A, Q)
        G0 = B0 @ B0.T
        ev0 = np.linalg.eigvalsh(G0)
        LH0 = ev0[1] / ev0[0]
        M = IntegerMatrix.from_matrix(B0.tolist())
        LLL.reduction(M)
        Blll = np.array([[M[i, j] for j in range(M.ncols)] for i in range(M.nrows)])
        G = Blll @ Blll.T
        ev = np.linalg.eigvalsh(G)
        LH = ev[1] / ev[0]
        sigma, mu = gso_mu(Blll)
        MM = mu @ mu.T
        evm = np.linalg.eigvalsh(MM)
        kappa = evm[1] / evm[0]
        LHs.append(LH); kaps.append(kappa); LH0s.append(LH0)
    LHs = np.array(LHs); kaps = np.array(kaps); LH0s = np.array(LH0s)
    print(f"===== {'中心化' if centered else '非中心化'} d={d} N=20 (seed 0-19) =====")
    print(f"原始 Λ_H:  mean={LH0s.mean():.6f} std={LH0s.std():.2e}")
    print(f"LLL后 Λ_H: mean={LHs.mean():.3f} std={LHs.std():.3f} CV={LHs.std()/LHs.mean():.3f} [{LHs.min():.3f}, {LHs.max():.3f}]")
    print(f"κ(μ):      mean={kaps.mean():.3f} CV={kaps.std()/kaps.mean():.3f} [{kaps.min():.3f}, {kaps.max():.3f}]")
    print(f"θ=Λ_H/κ:   mean={(LHs/kaps).mean():.3f}")
    print(f"P(Λ_H>3.6)={np.mean(LHs>3.6):.3f}  P(Λ_H<1.02)={np.mean(LHs<1.02):.3f}")
    print()
