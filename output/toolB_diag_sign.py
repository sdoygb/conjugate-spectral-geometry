"""诊断：REAL vs MOD vs CENTERED 的符号偏置来源。
d=64, N=8。输出：Gram 核结构、初始 GSO 符号、sigma 序列、LLL 后 mu 符号、b*/b 分量符号。
"""
import numpy as np, json, sys
from fpylll import IntegerMatrix, LLL

Q = 3329

def build_A(row, mode):
    d = len(row)
    A = np.zeros((d, d), dtype=np.int64)
    for i in range(d):
        for k in range(d):
            r = (k - i) % d
            if mode == 'real':
                val = row[r]
                if k < i:
                    val = -val
            elif mode == 'mod':
                val = row[r]
                if k < i:
                    val = (-val) % Q
            elif mode == 'cent':
                val = row[r] - Q // 2
                if k < i:
                    val = -val
            A[i, k] = val
    return A

def build_B0(row, mode):
    d = len(row)
    A = build_A(row, mode)
    B = np.zeros((2*d, 2*d), dtype=np.int64)
    B[:d, :d] = A
    B[:d, d:] = np.eye(d, dtype=np.int64)
    B[d:, d:] = Q * np.eye(d, dtype=np.int64)
    return B, A

def gso_mu(B):
    n = B.shape[0]
    Bf = B.astype(np.float64)
    bstar = np.zeros_like(Bf)
    mu = np.zeros((n, n))
    sig = np.zeros(n)
    for i in range(n):
        if i == 0:
            bstar[0] = Bf[0].copy()
            sig[0] = np.dot(Bf[0], Bf[0])
            continue
        num = Bf[i] @ bstar[:i].T
        mu[i, :i] = num / sig[:i]
        bstar[i] = Bf[i] - mu[i, :i] @ bstar[:i]
        sig[i] = np.dot(bstar[i], bstar[i])
    np.fill_diagonal(mu, 1.0)
    return sig, mu, bstar

def lll(B0):
    n = B0.shape[0]
    M = IntegerMatrix(n, n)
    for i in range(n):
        for j in range(n):
            M[i, j] = int(B0[i, j])
    LLL.reduction(M)
    B = np.array([[M[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    return B

def dc_stats(mu, n, dmax):
    idx = np.tril_indices(n, -1)
    iu, ju = idx
    dc = np.minimum(np.abs(iu - ju), n - np.abs(iu - ju))
    absv = np.abs(mu[iu, ju])
    nz = absv > 1e-12
    pos = mu[iu, ju] > 1e-12
    out = {}
    for dcv in [1, 2, 4, 8, 16, 32]:
        m = dc == dcv
        if m.sum() == 0:
            continue
        out[f'E{dcv}'] = float(absv[m].mean())
        out[f'P0{dcv}'] = float((~nz[m]).mean())
        if nz[m].sum() > 0:
            out[f'Pp{dcv}'] = float(pos[m][nz[m]].mean())
    return out

def run(seed, mode, d):
    rng = np.random.default_rng(seed)
    row = rng.integers(0, Q, d)
    B0, A = build_B0(row, mode)
    n = 2 * d
    # 初始 GSO
    sig0, mu0, bs0 = gso_mu(B0)
    # Gram 核结构（A 块，线性距离）
    G = A.astype(np.float64)
    norm2 = np.diag(G @ G.T).mean()
    gram_delta = {}
    for D in [1, 2, 4, 8, 16, 24, 31]:
        cnt, s = 0, 0.0
        for i in range(d - D):
            s += float(np.dot(G[i], G[i + D]))
            cnt += 1
        gram_delta[D] = s / cnt / norm2 if cnt else 0.0
    # LLL
    B = lll(B0)
    sig, mu, bs = gso_mu(B)
    stats = dc_stats(mu, n, d)
    stats0 = dc_stats(mu0, n, d)
    # b* 与 b 的分量符号
    pos_bs = float((bs > 0).mean())
    pos_b = float((B > 0).mean())
    # sigma 序列摘要（LLL 前/后，log 尺度）
    def sig_sum(sigv):
        s = np.sort(sigv)
        return dict(min=float(s[0]), q1=float(s[n//4]), med=float(s[n//2]),
                    max=float(s[-1]), ratio=float(s[-1] / max(s[0], 1e-30)))
    return dict(seed=seed, mode=mode, gram_delta=gram_delta,
                init=stats0, out=stats,
                pos_bs=pos_bs, pos_b=pos_b,
                sig0=sig_sum(sig0), sig=sig_sum(sig),
                sig0_raw=[float(x) for x in sig0[:10]],
                sig_raw=[float(x) for x in sig[:10]])

if __name__ == '__main__':
    d = 64
    seeds = [1, 2, 3, 4, 5, 6, 7, 8]
    for mode in ['real', 'mod', 'cent']:
        for seed in seeds:
            r = run(seed, mode, d)
            print(json.dumps(r))
            sys.stdout.flush()
