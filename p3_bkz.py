"""P3 扩展：BKZ 归约深度 vs 结构信号（伪装 diag 格 vs 随机格）"""
import numpy as np
from numpy.linalg import eigvalsh, det
from fpylll import IntegerMatrix, LLL, BKZ
import sys, time

def features(B):
    G = B @ B.T
    ev = np.sort(eigvalsh(G))
    ev = ev[ev > 1e-12]
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2/lam1
    Lmax = lamn/lam1
    dd = np.diff(ev)
    num = np.minimum(dd[:-1], dd[1:]); den = np.maximum(dd[:-1], dd[1:])
    gr = np.divide(num, den, out=np.zeros_like(num), where=den>0)
    le = np.log(ev)
    f = [np.log10(LH), np.log10(Lmax), np.mean(gr), np.std(gr), np.std(le),
         (np.mean(le)-np.min(le))/(np.max(le)-np.min(le)+1e-12)]
    n = B.shape[0]
    detB = abs(round(np.linalg.det(B)))
    gh = np.sqrt(n/(2*np.pi*np.e)) * detB**(1/n)
    l1 = np.sqrt(lam1)
    f.append(np.log10(l1/gh + 1e-300))
    return np.array(f)

def diag_B(n, M):
    B = np.eye(n) * M; B[0,0] = 1
    return B

def negacyclic(a):
    n = len(a); M = np.zeros((n,n))
    for i in range(n):
        M[i] = np.roll(a, i)
        if i > 0: M[i,:i] *= -1
    return M

def random_B(n, q=3329, seed=0):
    rng = np.random.default_rng(seed)
    d = 2*n
    A = np.zeros((d,d))
    A[:n,:n] = negacyclic(rng.integers(0,q,n))
    A[n:,:n] = negacyclic(rng.integers(0,q,n))
    A[:n,n:] = negacyclic(rng.integers(0,q,n))
    A[n:,n:] = negacyclic(rng.integers(0,q,n))
    B = np.zeros((2*d, 2*d))
    B[:d,:d] = A; B[:d,d:] = np.eye(d); B[d:,d:] = q*np.eye(d)
    return B

def random_unimodular(n, seed, nops_factor=10, K=1):
    rng = np.random.default_rng(seed)
    U = np.eye(n, dtype=int)
    for _ in range(nops_factor * n):
        op = rng.integers(0, 3); i, j = rng.integers(0, n, 2)
        if i == j: continue
        if op == 0: U[[i,j]] = U[[j,i]]
        elif op == 1:
            k = rng.integers(-K, K+1)
            if k != 0: U[i] += k * U[j]
        else: U[i] *= -1
    return U

def lll_reduce(B):
    M = IntegerMatrix.from_matrix(np.round(B).astype(int).tolist())
    LLL.reduction(M)
    n, d = M.nrows, M.ncols
    return np.array([[M[i,j] for j in range(d)] for i in range(n)], dtype=float)

def bkz_reduce(B, beta):
    M = IntegerMatrix.from_matrix(np.round(B).astype(int).tolist())
    BKZ.reduction(M, BKZ.Param(block_size=beta, max_loops=4))
    n, d = M.nrows, M.ncols
    return np.array([[M[i,j] for j in range(d)] for i in range(n)], dtype=float)

def report(tag, B0, betas):
    print(f"--- {tag} ---")
    for red_name, red_fn in [("LLL", lll_reduce), ("raw", lambda B: B)]:
        B = red_fn(B0)
        f = features(B)
        print(f"  {red_name:5s}: log10LH={f[0]:8.4f}  l1_norm={f[6]:8.4f}")
    for beta in betas:
        t0 = time.time()
        B = bkz_reduce(B0, beta)
        f = features(B)
        print(f"  BKZ-{beta:2d}   : log10LH={f[0]:8.4f}  l1_norm={f[6]:8.4f}  ({time.time()-t0:.1f}s)")

# 伪装 diag 格
for n, M in [(8,10),(8,100),(16,10),(16,100)]:
    B0 = random_unimodular(n, seed=7) @ diag_B(n, M)
    report(f"disguised diag n={n} M={M}", B0, [2,5,10] if n==8 else [2,5,10,15])

# 随机格
for n in [8,16]:
    report(f"random n={n}", random_B(n, seed=3), [2,5,10] if n==8 else [2,5,10,15])

# 标准 diag 对照（不变量验证）
for n, M in [(16,10),(16,100)]:
    report(f"plain diag n={n} M={M}", diag_B(n, M), [2,5,10,15])
