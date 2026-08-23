"""P3-BKZ 修正版：结构指纹 = 归约基第一行长度/GH（λ₁_est/GH）"""
import numpy as np
from numpy.linalg import eigvalsh
from fpylll import IntegerMatrix, LLL, BKZ
import time

def feats(B):
    G = B @ B.T
    ev = np.sort(eigvalsh(G))
    ev = ev[ev > 1e-12]
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2/lam1
    dd = np.diff(ev)
    num = np.minimum(dd[:-1], dd[1:]); den = np.maximum(dd[:-1], dd[1:])
    gr = np.divide(num, den, out=np.zeros_like(num), where=den>0)
    le = np.log(ev)
    return np.log10(LH), np.mean(gr), np.std(le)

def gh_est(B):
    n = B.shape[0]
    detB = abs(round(np.linalg.det(B)))
    return np.sqrt(n/(2*np.pi*np.e)) * detB**(1/n)

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
    for bi in range(2):
        for bj in range(2):
            A[bi*n:(bi+1)*n, bj*n:(bj+1)*n] = negacyclic(rng.integers(0,q,n))
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

def reduce(B, beta=None):
    M = IntegerMatrix.from_matrix(np.round(B).astype(int).tolist())
    if beta is None: LLL.reduction(M)
    else: BKZ.reduction(M, BKZ.Param(block_size=beta, max_loops=4))
    n, d = M.nrows, M.ncols
    return np.array([[M[i,j] for j in range(d)] for i in range(n)], dtype=float)

def report(tag, B0, betas):
    gh = gh_est(B0)
    print(f"--- {tag} (GH={gh:.1f}) ---")
    for name, beta in [("LLL", None)] + [(f"BKZ-{b}", b) for b in betas]:
        B = reduce(B0, beta)
        lh, gr, sl = feats(B)
        b1 = np.linalg.norm(B[0])
        print(f"  {name:6s}: log10LH={lh:7.4f}  l1/GH={np.log10(b1/gh):7.4f}  (b1={b1:9.4f})")

for n, M in [(8,10),(8,100),(16,10),(16,100)]:
    B0 = random_unimodular(n, seed=7) @ diag_B(n, M)
    report(f"disguised diag n={n} M={M}", B0, [5,10] if n==8 else [5,10,15])

for n in [8,16]:
    report(f"random n={n}", random_B(n, seed=3), [5,10] if n==8 else [5,10,15])
