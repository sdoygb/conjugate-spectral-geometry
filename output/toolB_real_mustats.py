"""工具 B：REAL-mode（实负循环 [0,q-1] 不取模）下的 μ 统计——P2 标定基准的完整验证。
对每个 seed：B0 = [[A, I],[0, qI]]，A 为实负循环（negacyclic_real），fpylll LLL delta=0.99。
输出 per-sample：Λ_H, κ(μ), θ, MM^T 谱 + 循环距离曲线（E|mu|, 零率, 非零均值, P(+)）。
每样本立即写 JSONL（超时安全）。
用法: python toolB_real_mustats.py <start_seed> <n_samples> [out_prefix]
"""
import sys, json, time
import numpy as np
from fpylll import IntegerMatrix, LLL

Q = 3329
d = int(sys.argv[4]) if len(sys.argv) > 4 else 256
n = 2 * d

def negacyclic_real(row, q):
    d0 = len(row)
    A = np.zeros((d0, d0), dtype=np.int64)
    for i in range(d0):
        for j in range(d0):
            v = row[(j - i) % d0]
            A[i, j] = v if j >= i else -v
    return A

def gso_mu(B):
    n0 = B.shape[0]
    Bf = B.astype(np.float64)
    bstar = np.zeros_like(Bf)
    mu = np.zeros((n0, n0))
    sigma = np.zeros(n0)
    for i in range(n0):
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

def dc_curves(mu):
    """循环距离曲线：dc = min(|i-j|, n-|i-j|) ∈ [1, d]"""
    n = mu.shape[0]
    idx = np.arange(n)
    ri, ci = np.meshgrid(idx, idx, indexing='ij')
    dc = np.minimum(np.abs(ri - ci), n - np.abs(ri - ci))
    dc = dc[np.tril_indices(n, -1)]           # 只取下三角（j < i，μ 的定义域）
    vals = mu[np.tril_indices(n, -1)]
    absv = np.abs(vals)
    counts = np.bincount(dc, minlength=n)
    E = np.bincount(dc, weights=absv, minlength=n) / np.maximum(counts, 1)
    zero = np.bincount(dc, weights=(absv == 0).astype(float), minlength=n) / np.maximum(counts, 1)
    nz_mask = absv > 0
    nz_counts = np.bincount(dc, weights=nz_mask.astype(float), minlength=n)
    nz_sum = np.bincount(dc, weights=np.where(nz_mask, absv, 0.0), minlength=n)
    nz_mean = nz_sum / np.maximum(nz_counts, 1)
    pos = np.bincount(dc, weights=((vals > 0) & nz_mask).astype(float), minlength=n) / np.maximum(nz_counts, 1)
    dd = n // 2
    return E[1:dd+1], zero[1:dd+1], nz_mean[1:dd+1], pos[1:dd+1]

def main():
    start = int(sys.argv[1]); cnt = int(sys.argv[2])
    prefix = sys.argv[3] if len(sys.argv) > 3 else "toolB_real_mustats"
    out = f"{prefix}.jsonl"
    for s in range(start, start + cnt):
        t0 = time.time()
        rng = np.random.default_rng(s)
        a = rng.integers(0, Q, d)
        A = negacyclic_real(a, Q)
        B0 = np.zeros((n, n), dtype=np.int64)
        B0[:d, :d] = A
        B0[:d, d:] = np.eye(d, dtype=np.int64)
        B0[d:, d:] = Q * np.eye(d, dtype=np.int64)
        G0 = B0.astype(np.float64) @ B0.astype(np.float64).T
        ev0 = np.linalg.eigvalsh(G0)
        LH0 = float(ev0[1] / ev0[0])
        M = IntegerMatrix.from_matrix(B0.tolist())
        LLL.reduction(M, delta=0.99)
        B = np.array([[M[i, j] for j in range(M.ncols)] for i in range(M.nrows)])
        G = B.astype(np.float64) @ B.astype(np.float64).T
        ev = np.linalg.eigvalsh(G)
        LH = float(ev[1] / ev[0])
        sig, mu = gso_mu(B)
        MM = mu @ mu.T
        evm = np.linalg.eigvalsh(MM)
        kap = float(evm[1] / evm[0])
        E, zero, nz_mean, pos = dc_curves(mu)
        rec = {"seed": s, "LH0": LH0, "LH": LH, "kappa": kap,
               "theta": LH / kap,
               "lam1_MM": float(evm[0]), "lam2_MM": float(evm[1]),
               "lammax_MM": float(evm[-1]),
               "sum_mu2": float((mu[np.tril_indices(n, -1)] ** 2).sum()), "trace_MM": float(np.trace(MM)),
               "dc_E": E.tolist(), "dc_zero": zero.tolist(),
               "dc_nz": nz_mean.tolist(), "dc_pos": pos.tolist()}
        with open(out, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"seed {s}: Λ_H={LH:.3f} κ={kap:.3f} θ={LH/kap:.3f} ({time.time()-t0:.0f}s)", flush=True)
    print(f"BATCH DONE [{start},{start+cnt})", flush=True)

if __name__ == "__main__":
    main()
