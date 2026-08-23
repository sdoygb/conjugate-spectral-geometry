#!/usr/bin/env python3
# P3: 偏离检测 —— 结构化格 vs 随机化格的谱统计分类 (v2, 修复 gap nan / n=2)
import numpy as np
from numpy.linalg import eigvalsh

def diag_B(n, M):
    B = np.eye(n) * M
    B[0, 0] = 1.0
    return B

def negacyclic(a):
    n = len(a)
    M = np.zeros((n, n))
    for i in range(n):
        M[i] = np.roll(a, i)
        if i > 0:
            M[i, :i] *= -1
    return M

def mlkem_B(n, k, q, seed):
    rng = np.random.default_rng(seed)
    d = k * n
    A = np.zeros((d, d))
    for bi in range(k):
        for bj in range(k):
            A[bi*n:(bi+1)*n, bj*n:(bj+1)*n] = negacyclic(rng.integers(0, q, n))
    B = np.zeros((2*d, 2*d))
    B[:d, :d] = A
    B[:d, d:] = np.eye(d)
    B[d:, d:] = q * np.eye(d)
    return B

def features(B):
    G = B @ B.T
    ev = np.sort(eigvalsh(G))
    ev = ev[ev > 1e-12]
    if len(ev) < 2:
        return None
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2 / lam1
    Lmax = lamn / lam1
    if len(ev) >= 3:
        d = np.diff(ev)
        num = np.minimum(d[:-1], d[1:])
        den = np.maximum(d[:-1], d[1:])
        gr = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
        mg, sg = np.mean(gr), np.std(gr)
    else:
        mg, sg = 0.0, 0.0
    le = np.log(ev)
    rng_ = np.ptp(le)
    skew = (np.mean(le) - np.median(le)) / (np.std(le) + 1e-12)
    return np.array([np.log10(LH), np.log10(Lmax), mg, sg,
                     np.std(le) / (rng_ + 1e-12), skew])

def kNN_predict(Xtr, ytr, Xte, k=5):
    preds = []
    for x in Xte:
        dist = np.sum((Xtr - x)**2, axis=1)
        idx = np.argsort(dist)[:k]
        votes = ytr[idx]
        preds.append(1 if votes.sum() >= (k + 1) // 2 else 0)
    return np.array(preds)

def cv5_knn(X, y, k=5):
    n = len(y)
    idx = np.random.default_rng(42).permutation(n)
    folds = np.array_split(idx, 5)
    accs = []
    for f in folds:
        te_mask = np.zeros(n, bool); te_mask[f] = True
        pred = kNN_predict(X[~te_mask], y[~te_mask], X[te_mask], k)
        accs.append(np.mean(pred == y[te_mask]))
    return np.mean(accs)

# ---------- 样本 ----------
S_feat, S_meta = [], []
for n in [3, 4, 8, 16, 32, 64]:
    for M in [10, 100, 1000]:
        for s in range(5):
            f = features(diag_B(n, M))
            if f is not None:
                S_feat.append(f); S_meta.append((n, M))
S_feat = np.array(S_feat)

R_feat, R_meta = [], []
for n in [4, 8, 16, 32]:
    for s in range(10):
        f = features(mlkem_B(n, 2, 3329, 1000 + s))
        if f is not None:
            R_feat.append(f); R_meta.append(n)
R_feat = np.array(R_feat)

I_feat, I_s = [], []
for n in [8, 16, 32]:
    for sval in [0.1, 0.5, 1, 2, 5, 10, 50, 100]:
        rng = np.random.default_rng(int(sval * 100) + n)
        for rep in range(8):
            B = diag_B(n, 100)
            E = rng.uniform(-1, 1, (n, n))
            np.fill_diagonal(E, 0)
            f = features(B + sval * E)
            if f is not None:
                I_feat.append(f); I_s.append(sval)
I_feat = np.array(I_feat); I_s = np.array(I_s)

# ---------- 1. 分布 ----------
print("=== P3 谱统计: 两类分布 (均值±std) ===")
names = ["log10 L_H", "log10 L_max", "mean gap", "std gap", "logspec std", "skew"]
for i, nm in enumerate(names):
    print(f"{nm:12s}  S: {S_feat[:,i].mean():9.3f}±{S_feat[:,i].std():8.3f}   "
          f"R: {R_feat[:,i].mean():9.3f}±{R_feat[:,i].std():8.3f}")

muS, muR = S_feat.mean(0), R_feat.mean(0)
covS, covR = np.cov(S_feat.T), np.cov(R_feat.T)
W = (covS + covR) / 2
d2 = (muS - muR) @ np.linalg.inv(W + 1e-6 * np.eye(6)) @ (muS - muR)
print(f"\nMahalanobis 距离^2 (S vs R): {d2:.1f}")

# ---------- 2. 二分类 ----------
X = np.vstack([S_feat, R_feat])
y = np.array([1]*len(S_feat) + [0]*len(R_feat))
acc = cv5_knn(X, y)
print(f"kNN(5) 5折 准确率: {acc*100:.1f}%  (n_S={len(S_feat)}, n_R={len(R_feat)})")

G2 = features(diag_B(2, 100))
pred2 = kNN_predict(X, y, G2.reshape(1, -1))
print(f"10.56 表 n=2, M=100 格分类: {'结构化' if pred2[0] else '随机'} (应: 结构化)")

# ---------- 3. 灵敏度 ----------
print("\n=== 灵敏度: diag + s*E 被分为结构化的比例 (M=100, Lambda_H=1e4) ===")
print("扰动 s      P(结构化)")
for sval in [0.1, 0.5, 1, 2, 5, 10, 50, 100]:
    mask = I_s == sval
    pred = kNN_predict(X, y, I_feat[mask])
    frac = pred.mean()
    bar = "#" * int(frac * 40)
    print(f"{sval:8.1f}  {frac:8.3f}  {bar}")

for sval in [0.1, 0.5, 1, 2, 5, 10, 50, 100]:
    mask = I_s == sval
    pred = kNN_predict(X, y, I_feat[mask])
    if pred.mean() < 0.5:
        print(f"\n检测极限: s* ≈ {sval} (P(结构化) < 0.5, M=100)")
        break

# ---------- 4. 单特征分离 ----------
print(f"\n单特征 log10 L_H:  S ∈ [{S_feat[:,0].min():.3f}, {S_feat[:,0].max():.3f}]  "
      f"R ∈ [{R_feat[:,0].min():.6f}, {R_feat[:,0].max():.6f}]")
