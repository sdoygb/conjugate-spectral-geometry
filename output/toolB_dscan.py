"""工具 B d 扫描：验证循环距离标度律与 κ 分布（Gamma 形状）随 d 的普适性
用法: python toolB_dscan.py <d> <N> [seed]
输出: output/toolB_dscan_{d}.npz  (每样本: LH, kappa, theta_ratio, lam1/lam2/lammax_MM,
      循环曲线 dc=1..d: E|mu|, 稀疏率, 非零均值, P(+))
"""
import sys
import numpy as np
from fpylll import IntegerMatrix, LLL

Q = 3329

def negacyclic_from_row(a, q):
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
    """向量化 GSO：σ（长度²）与 μ（单位下三角系数）"""
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

def main():
    d = int(sys.argv[1]); N = int(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    rng = np.random.default_rng(seed)
    n = 2 * d
    out = dict(d=d, N=N)
    LHs, kaps, thetas = [], [], []
    lam1s, lam2s, lamaxs = [], [], []
    # 循环曲线聚合（累加器）
    dc_E = np.zeros(d + 1); dc_cnt = np.zeros(d + 1)
    dc_zero = np.zeros(d + 1)
    dc_nz = np.zeros(d + 1); dc_nz_cnt = np.zeros(d + 1)
    dc_pos = np.zeros(d + 1); dc_pos_cnt = np.zeros(d + 1)
    # 距离索引
    idx = np.arange(n)
    dc = np.minimum(np.abs(idx[:, None] - idx[None, :]), n - np.abs(idx[:, None] - idx[None, :]))
    for trial in range(N):
        a = rng.integers(0, Q, size=d)
        A = negacyclic_from_row(a, Q)
        B0 = build_B(A, Q)
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
        LHs.append(LH); kaps.append(kappa); thetas.append(LH / kappa)
        lam1s.append(evm[0]); lam2s.append(evm[1]); lamaxs.append(evm[-1])
        # 循环距离统计
        absmu = np.abs(mu)
        flat_dc = dc.ravel(); flat_abs = absmu.ravel(); flat_mu = mu.ravel()
        b = np.bincount(flat_dc, weights=flat_abs, minlength=d + 1)
        c = np.bincount(flat_dc, minlength=d + 1)
        dc_E += b; dc_cnt += c
        z = np.bincount(flat_dc, weights=(flat_abs == 0).astype(float), minlength=d + 1)
        dc_zero += z
        nzmask = flat_mu != 0
        nz_abs = np.where(nzmask, flat_abs, 0.0)
        b2 = np.bincount(flat_dc, weights=nz_abs, minlength=d + 1)
        c2 = np.bincount(flat_dc, weights=nzmask.astype(float), minlength=d + 1)
        dc_nz += b2; dc_nz_cnt += c2
        pmask = (flat_mu > 0) & nzmask
        b3 = np.bincount(flat_dc, weights=pmask.astype(float), minlength=d + 1)
        dc_pos += b3; dc_pos_cnt += c2  # 分母 = 非零数
    out['LH'] = np.array(LHs); out['kappa'] = np.array(kaps)
    out['theta'] = np.array(thetas)
    out['lam1_MM'] = np.array(lam1s); out['lam2_MM'] = np.array(lam2s)
    out['lammax_MM'] = np.array(lamaxs)
    out['dc_E'] = dc_E[1:] / dc_cnt[1:]          # E|μ|(dc), dc=1..d
    out['dc_zero'] = dc_zero[1:] / dc_cnt[1:]    # P(μ=0)
    out['dc_nz'] = dc_nz[1:] / np.maximum(dc_nz_cnt[1:], 1e-30)  # 非零均值
    out['dc_pos'] = dc_pos[1:] / np.maximum(dc_pos_cnt[1:], 1e-30)  # P(μ>0 | μ≠0)
    np.savez(f"toolB_dscan_{d}.npz", **out)
    print(f"d={d} N={N} done: Λ_H mean={np.mean(LHs):.3f} CV={np.std(LHs)/np.mean(LHs):.3f} "
          f"κ mean={np.mean(kaps):.3f} CV={np.std(kaps)/np.mean(kaps):.3f} θ={np.mean(thetas):.3f}")

if __name__ == "__main__":
    main()
