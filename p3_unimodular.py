# P3 扩展：随机幺模扰动的谱分离检测（10.56 开放问题 4 第一部分）
# 结构化格 diag(1,M,...,M) 用随机幺模 U 伪装（B' = U·B，同一格，非标准嵌入）
# 检测管线：直接谱统计 vs LLL 解伪装后谱统计
import numpy as np
from numpy.linalg import eigvalsh
from fpylll import IntegerMatrix, LLL
import itertools

def features(B):
    """6 维谱统计特征（与 P3 一致）"""
    G = B @ B.T
    ev = np.sort(eigvalsh(G))
    ev = ev[ev > 1e-12]
    if len(ev) < 3:
        return None
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2/lam1
    Lmax = lamn/lam1
    d = np.diff(ev)
    num = np.minimum(d[:-1], d[1:]); den = np.maximum(d[:-1], d[1:])
    gr = np.divide(num, den, out=np.zeros_like(num), where=den>0)
    le = np.log(ev)
    return np.array([np.log10(LH), np.log10(Lmax), np.mean(gr), np.std(gr),
                     np.std(le), (np.mean(le)-np.min(le))/(np.max(le)-np.min(le)+1e-12)])

def diag_B(n, M):
    B = np.eye(n) * M
    B[0,0] = 1.0
    return B

def random_unimodular(n, seed, nops_factor=3, K=1):
    """从 I 出发的随机行操作序列 -> 随机幺模矩阵（det=±1）"""
    rng = np.random.default_rng(seed)
    U = np.eye(n, dtype=int)
    nops = nops_factor * n
    for _ in range(nops):
        op = rng.integers(0, 3)
        i, j = rng.integers(0, n, 2)
        if i == j:
            continue
        if op == 0:
            U[[i,j]] = U[[j,i]].copy()  # 行交换
        elif op == 1:
            k = rng.integers(-K, K+1)
            if k != 0:
                U[i] += k * U[j]        # 行加整数倍
        else:
            U[i] *= -1                   # 行取负
    return U

def lll_reduce(B):
    M = IntegerMatrix.from_matrix(np.round(B).astype(int).tolist())
    LLL.reduction(M)
    n, d = M.nrows, M.ncols
    return np.array([[M[i,j] for j in range(d)] for i in range(n)], dtype=float)

# ---------- 训练集（与 P3 同构型）----------
S_feats, R_feats, S_label, R_label = [], [], 1, 0
for n in [4, 8, 16, 32]:
    for M in [10, 100, 1000]:
        for seed in range(10):
            f = features(diag_B(n, M))
            if f is not None: S_feats.append(f)
# 随机类：ML-KEM 风格负循环块格（n=4..32, k=2, q=3329）
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
    B[:d,:d] = A; B[:d,d:] = np.eye(d); B[d:,d:] = q*np.eye(d)
    return B
for n in [4, 8, 16, 32]:
    for seed in range(15):
        f = features(mlkem_B(n, 2, 3329, seed))
        if f is not None: R_feats.append(f)
S_feats = np.array(S_feats); R_feats = np.array(R_feats)
train_X = np.vstack([S_feats, R_feats])
train_y = np.array([S_label]*len(S_feats) + [R_label]*len(R_feats))
print(f"训练集: S={len(S_feats)}, R={len(R_feats)}")

# kNN (k=5)
def knn_predict(X, k=5):
    out = []
    for x in X:
        d = np.linalg.norm(train_X - x, axis=1)
        idx = np.argsort(d)[:k]
        out.append(np.mean(train_y[idx]))
    return np.array(out)

# 自检（留一法粗略：直接对训练集预测）
acc_self = np.mean((knn_predict(train_X) > 0.5) == train_y)
print(f"训练集自检准确率: {acc_self:.3f}")

# ---------- 伪装实验 ----------
print("\n=== 随机幺模伪装：直接检测 vs LLL 解伪装 ===")
print(f"{'n':>3} {'M':>5} {'ops':>4} {'K':>3} | {'直接检测率':>8} {'直接ΛH(log10)':>12} | {'LLL后检测率':>10} {'LLL后ΛH(log10)':>14}")
for n, M, c, K in itertools.product([8, 16, 32], [10, 100], [1, 3, 10], [1, 10]):
    det_direct, det_lll = [], []
    LH_direct, LH_lll = [], []
    for seed in range(10):
        B = diag_B(n, M)
        U = random_unimodular(n, seed*1000+n, nops_factor=c, K=K)
        Bp = U.astype(float) @ B          # 伪装基（同一格）
        fd = features(Bp)
        det_direct.append(knn_predict(fd.reshape(1,-1))[0] if fd is not None else 0)
        if fd is not None: LH_direct.append(fd[0])
        Blll = lll_reduce(Bp)
        fl = features(Blll)
        det_lll.append(knn_predict(fl.reshape(1,-1))[0] if fl is not None else 0)
        if fl is not None: LH_lll.append(fl[0])
    print(f"{n:>3} {M:>5} {c:>4} {K:>3} | {np.mean(det_direct)*100:7.1f}% {np.mean(LH_direct):12.2f} | {np.mean(det_lll)*100:9.1f}% {np.mean(LH_lll):14.2f}")

# ---------- 对照：随机格走 LLL 不产生结构 ----------
print("\n=== 对照：随机格 LLL 前后检测（应始终判为随机）===")
for n in [8, 16]:
    d_before, d_after = [], []
    for seed in range(10):
        B = mlkem_B(n, 2, 3329, seed+5000)
        fb = features(B)
        d_before.append(knn_predict(fb.reshape(1,-1))[0])
        Bl = lll_reduce(B)
        fl = features(Bl)
        d_after.append(knn_predict(fl.reshape(1,-1))[0])
    print(f"n={n}: 直接 {np.mean(d_before)*100:.1f}% 判结构 | LLL后 {np.mean(d_after)*100:.1f}% 判结构（应≈0）")
