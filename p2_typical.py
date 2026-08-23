import numpy as np
from numpy.linalg import eigvalsh, norm
from fpylll import IntegerMatrix, LLL

def negacyclic(a):
    n = len(a); M = np.zeros((n,n))
    for i in range(n):
        M[i] = np.roll(a, i)
        if i > 0: M[i,:i] *= -1
    return M

def mlkem_B(n, k, q, seed):
    rng = np.random.default_rng(seed)
    d = k*n
    A = np.zeros((d,d))
    for bi in range(k):
        for bj in range(k):
            A[bi*n:(bi+1)*n, bj*n:(bj+1)*n] = negacyclic(rng.integers(0,q,n))
    B = np.zeros((2*d, 2*d))
    B[:d,:d] = A
    B[:d,d:] = np.eye(d)
    B[d:,d:] = q*np.eye(d)
    return B

def gram_stats(G):
    ev = np.sort(eigvalsh(G)); ev = ev[ev > 1e-12]
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2/lam1; Lmax = lamn/lam1
    dd = np.diff(ev)
    num = np.minimum(dd[:-1], dd[1:]); den = np.maximum(dd[:-1], dd[1:])
    gr = np.divide(num, den, out=np.zeros_like(num), where=den>0)
    le = np.log(ev)
    return dict(LH=LH, Lmax=Lmax, gap_mean=float(np.mean(gr)), gap_std=float(np.std(gr)),
                lspec_std=float(np.std(le)), skew=float((np.mean(le)-np.min(le))/(np.max(le)-np.min(le)+1e-12)),
                lmin=float(lam1), lmax=float(lamn))

def lll_stats(B, q, k, n):
    M = IntegerMatrix.from_matrix(np.round(B).astype(int).tolist())
    LLL.reduction(M)
    d = M.nrows
    Br = np.array([[M[i,j] for j in range(d)] for i in range(d)], dtype=float)
    G = Br @ Br.T
    ev = np.sort(eigvalsh(G)); ev = ev[ev > 1e-12]
    b1 = norm(Br[0])
    dd = 2*k*n  # 格维度
    gh = np.sqrt(dd/(2*np.pi*np.e)) * q**0.5  # det^{1/dd} = q^{1/2}
    return dict(LH_lll=float(ev[1]/ev[0]), l1_gh=float(np.log10(b1/gh)), b1=float(b1), gh=float(gh))

N = 20
rows = []
for seed in range(N):
    B = mlkem_B(256, 1, 3329, seed)
    gs = gram_stats(B @ B.T)
    ls = lll_stats(B, 3329, 1, 256)
    rows.append({**gs, **ls})
    print(f"seed {seed}: rawLH={gs['LH']:.6f} LLL_LH={ls['LH_lll']:.4f} l1_gh={ls['l1_gh']:.4f} b1={ls['b1']:.1f} gh={ls['gh']:.1f}", flush=True)

print("\n===== 汇总 (N=20) =====")
keys = list(rows[0].keys())
for key in keys:
    vals = np.array([r[key] for r in rows])
    mu, sd = np.mean(vals), np.std(vals)
    cv = sd/abs(mu) if mu != 0 else float('nan')
    print(f"{key:10s} mean={mu:12.4f} std={sd:12.4f} min={np.min(vals):12.4f} max={np.max(vals):12.4f} CV={cv:.4f}")

print("\n===== 3σ 异常检查 =====")
found = False
for key in keys:
    vals = np.array([r[key] for r in rows])
    mu, sd = np.mean(vals), np.std(vals)
    if sd == 0: continue
    outliers = [i for i,v in enumerate(vals) if abs(v-mu) > 3*sd]
    if outliers:
        found = True
        print(f"  {key}: 异常实例 {outliers} 值 {[round(vals[i],4) for i in outliers]}")
if not found: print("  全部 20 实例：无 3σ 异常")

print("\n===== 结构化对照 (diag 512 维) =====")
for M in [10, 100]:
    B = np.eye(512) * M; B[0,0] = 1
    gs = gram_stats(B @ B.T)
    ls = lll_stats(B, 3329, 1, 256)  # gh 计算用 q 但 diag 的 det 不同——重算
    dd = 512
    gh = np.sqrt(dd/(2*np.pi*np.e)) * M**((dd-1)/dd)
    b1 = 1.0
    print(f"diag M={M}: rawLH={gs['LH']:.4f} LLL_LH={ls['LH_lll']:.4f} l1_gh={np.log10(b1/gh):.4f} (b1={b1}, gh={gh:.1f})")
