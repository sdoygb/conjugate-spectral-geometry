#!/usr/bin/env python3
"""P3 收官：λ1/GH 指纹放回分类器，真实参数 n=256 验证区分度。
特征：6 维谱统计（LLL 归约基 Gram）+ λ1/GH（归约基第一行 / 高斯启发）。
训练集：小 n（diag S 类 vs q-ary R 类）；测试集：n=256（k=1，格 512 维）。
"""
import numpy as np
from numpy.linalg import eigvalsh
from fpylll import IntegerMatrix, LLL

def negacyclic(a):
    n = len(a); M = np.zeros((n, n), dtype=int)
    for i in range(n):
        M[i] = np.roll(a, i)
        if i > 0: M[i, :i] *= -1
    return M

def mlkem_B(n, q, seed):
    """k=1 负循环 MLWE 行格基，格维度 2n。det = q^n。"""
    rng = np.random.default_rng(seed)
    A = negacyclic(rng.integers(0, q, n))
    d = n
    B = np.zeros((2*d, 2*d), dtype=int)
    B[:d, :d] = A
    B[:d, d:] = np.eye(d, dtype=int)
    B[d:, d:] = q * np.eye(d, dtype=int)
    return B

def diag_B(n, M):
    B = np.eye(n, dtype=int) * M
    B[0, 0] = 1
    return B

def lll_reduce(B):
    M = IntegerMatrix.from_matrix(B.tolist())
    LLL.reduction(M)
    n, d = M.nrows, M.ncols
    return np.array([[M[i, j] for j in range(d)] for i in range(n)], dtype=float)

def features_lll(B, logdet):
    """LLL 归约后 7 维特征。logdet: det(B) 的自然对数（避免溢出）。"""
    Br = lll_reduce(B)
    n = Br.shape[0]
    G = Br @ Br.T
    ev = np.sort(eigvalsh(G)); ev = ev[ev > 1e-12]
    lam1, lam2, lamn = ev[0], ev[1], ev[-1]
    LH = lam2 / lam1; Lmax = lamn / lam1
    dd = np.diff(ev)
    num = np.minimum(dd[:-1], dd[1:]); den = np.maximum(dd[:-1], dd[1:])
    gr = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    le = np.log(ev)
    f = [np.log10(LH), np.log10(Lmax), np.mean(gr), np.std(gr),
         np.std(le), (np.mean(le) - np.min(le)) / (np.max(le) - np.min(le) + 1e-12)]
    # λ1/GH：归约基第一行长度 / 高斯启发（det 用对数域）
    b1 = np.linalg.norm(Br[0])
    gh = np.sqrt(n / (2 * np.pi * np.e)) * np.exp(logdet / n)
    f.append(np.log10(b1 / gh + 1e-300))
    return np.array(f)

def knn_predict(X_train, y_train, x, k=5):
    d = np.linalg.norm(X_train - x, axis=1)
    idx = np.argsort(d)[:k]
    votes = y_train[idx]
    return int(np.round(votes.mean())), d[idx].mean(), d.min()

# ---------- 训练集：小 n ----------
S, R = [], []
for n in [8, 16, 32, 64]:
    for M in [10, 100, 1000]:
        for seed in range(3):
            B = diag_B(n, M)
            logdet = (n - 1) * np.log(M)
            S.append(features_lll(B, logdet))
for n in [8, 16, 32, 64]:
    for seed in range(5):
        B = mlkem_B(n, 3329, seed)
        logdet = n * np.log(3329.0)
        R.append(features_lll(B, logdet))
X_train = np.array(S + R); y_train = np.array([1]*len(S) + [0]*len(R))
print(f"训练集: S={len(S)} R={len(R)}")
print(f"S λ1/GH 范围: [{X_train[y_train==1,6].min():.2f}, {X_train[y_train==1,6].max():.2f}]  "
      f"R λ1/GH 范围: [{X_train[y_train==0,6].min():.2f}, {X_train[y_train==0,6].max():.2f}]")
print(f"S log10LH 范围: [{X_train[y_train==1,0].min():.2f}, {X_train[y_train==1,0].max():.2f}]  "
      f"R log10LH 范围: [{X_train[y_train==0,0].min():.2f}, {X_train[y_train==0,0].max():.2f}]")
# 训练自检（留一）
acc = np.mean([knn_predict(X_train, y_train, X_train[i])[0] == y_train[i] for i in range(len(X_train))])
print(f"训练集留一准确率: {acc*100:.1f}%")

# ---------- 测试集：n=256（k=1，格 512 维） ----------
print("\n=== n=256 测试（k=1，格 512 维）===")
tests = []
for M in [10, 100]:
    for seed in range(2):
        B = diag_B(512, M)
        logdet = 511 * np.log(M)
        tests.append((f"diag M={M} s{seed}", 1, features_lll(B, logdet)))
for seed in range(3):
    B = mlkem_B(256, 3329, seed)
    logdet = 256 * np.log(3329.0)
    tests.append((f"ML-KEM n=256 s{seed}", 0, features_lll(B, logdet)))

for name, truth, x in tests:
    pred, dmean, dmin = knn_predict(X_train, y_train, x)
    ok = "✓" if pred == truth else "✗"
    print(f"{ok} {name:22s} 真={truth} 预测={pred}  kNN均距={dmean:.3f} 近邻距={dmin:.3f}  "
          f"λ1/GH={x[6]:+.2f} log10LH={x[0]:.2f}")
