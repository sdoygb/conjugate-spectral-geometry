"""工具 B：LLL 系数矩阵 μ 的统计结构
从 fpylll 输出重建 GSO 与 μ，统计：距离衰减、行/列能量、|μ| 分布、MM^T 谱
"""
import numpy as np
from fpylll import IntegerMatrix, LLL

Q = 3329
np.random.seed(42)

def negacyclic_from_row(a, q):
    """模 q 负循环矩阵，[0,q-1] 代表（非中心化——复现经验统计的表示）"""
    d = len(a)
    A = np.zeros((d, d), dtype=np.int64)
    for j in range(d):
        for k in range(d):
            s = (k - j) % d
            val = int(a[s])
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
    """从基 B 重建 GSO 长度² σ 与系数 μ（单位下三角）"""
    n = B.shape[0]
    B = B.astype(np.float64)
    bstar = np.zeros_like(B)
    mu = np.zeros((n, n))
    sigma = np.zeros(n)
    for i in range(n):
        bstar[i] = B[i].copy()
        for j in range(i):
            mu[i, j] = np.dot(B[i], bstar[j]) / np.dot(bstar[j], bstar[j])
            bstar[i] -= mu[i, j] * bstar[j]
        sigma[i] = np.dot(bstar[i], bstar[i])
    np.fill_diagonal(mu, 1.0)
    return sigma, mu

def run(d, N, tag):
    rows = []
    for trial in range(N):
        a = np.random.randint(0, Q, size=d)
        A = negacyclic_from_row(a, Q)
        B0 = build_B(A, Q)
        # 原始谱
        G0 = B0 @ B0.T
        ev0 = np.linalg.eigvalsh(G0)
        LH0 = ev0[1] / ev0[0]
        # fpylll LLL
        M = IntegerMatrix.from_matrix(B0.tolist())
        LLL.reduction(M)
        Blll = np.array([[M[i, j] for j in range(M.ncols)] for i in range(M.nrows)])
        # LLL 后谱
        G = Blll @ Blll.T
        ev = np.linalg.eigvalsh(G)
        LH = ev[1] / ev[0]
        # μ 重建
        sigma, mu = gso_mu(Blll)
        MM = mu @ mu.T
        evm = np.linalg.eigvalsh(MM)
        kappa = evm[1] / evm[0] if evm[0] > 1e-12 else np.nan
        # 统计量
        absmu = np.abs(mu)
        row_energy = np.sum(mu**2, axis=1)
        # 距离衰减：按 |i-j| 分箱平均 |μ|
        r_max = min(d // 2, 16)
        dist_decay = []
        for r in range(1, r_max + 1):
            vals = []
            for i in range(r, 2*d):
                vals.append(absmu[i, i - r])
            dist_decay.append(float(np.mean(vals)))
        rows.append(dict(d=d, trial=trial, LH0=float(LH0), LH=float(LH),
                         kappa=float(kappa), sigma_min=float(sigma.min()),
                         sigma_max=float(sigma.max()),
                         lam1_MM=float(evm[0]), lam2_MM=float(evm[1]),
                         lammax_MM=float(evm[-1]),
                         rowE_mean=float(row_energy.mean()),
                         rowE_max=float(row_energy.max()),
                         totalE=float(np.sum(mu**2)),
                         dist_decay=dist_decay,
                         absmu_mean=float(absmu.mean())))
    return rows

all_rows = []
for d, N in [(32, 40), (64, 25)]:
    all_rows += run(d, N, tag=f"d={d}")

# ===== 汇总输出 =====
for d in [32, 64]:
    rs = [r for r in all_rows if r['d'] == d]
    LHs = np.array([r['LH'] for r in rs])
    kaps = np.array([r['kappa'] for r in rs])
    LH0s = np.array([r['LH0'] for r in rs])
    rowE = np.array([r['rowE_mean'] for r in rs])
    rowEmax = np.array([r['rowE_max'] for r in rs])
    totE = np.array([r['totalE'] for r in rs])
    lam1 = np.array([r['lam1_MM'] for r in rs])
    lam2 = np.array([r['lam2_MM'] for r in rs])
    lammax = np.array([r['lammax_MM'] for r in rs])
    print(f"===== d={d} N={len(rs)} =====")
    print(f"原始 Λ_H:    mean={LH0s.mean():.4f}  (应为≈1, 非中心化时略>1)")
    print(f"LLL后 Λ_H:   mean={LHs.mean():.3f}  CV={LHs.std()/LHs.mean():.3f}  [{LHs.min():.3f}, {LHs.max():.3f}]")
    print(f"κ(μ):        mean={kaps.mean():.3f}  CV={kaps.std()/kaps.mean():.3f}  [{kaps.min():.3f}, {kaps.max():.3f}]")
    print(f"Λ_H/κ:       mean={(LHs/kaps).mean():.3f}  (θ₂/θ₁ 修正, 应≈1)")
    print(f"MM^T谱:      λ₁={lam1.mean():.4f}  λ₂={lam2.mean():.4f}  λ_max={lammax.mean():.1f}")
    print(f"μ行能量:     mean={rowE.mean():.3f}  max={rowEmax.max():.1f}  (2d-1行, 满均匀则≈(2d-1)/12·? )")
    print(f"μ总能量:     mean={totE.mean():.1f}  (n=2d, 均匀满则≈n²/24={ (4*d*d)/24:.0f})")
    # 距离衰减
    dd = np.array([r['dist_decay'] for r in rs])
    dd_mean = dd.mean(axis=0)
    print(f"距离衰减 |μ(i,i-r)| r=1..{len(dd_mean)}:")
    print("  " + "  ".join(f"r{r}:{v:.3f}" for r, v in enumerate(dd_mean, 1)))
    # 尾部
    print(f"P(κ>4)={np.mean(kaps>4):.3f}  P(Λ_H>4)={np.mean(LHs>4):.3f}  P(Λ_H<1.2)={np.mean(LHs<1.2):.3f}")
    print()
