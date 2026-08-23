"""第二轮诊断：符号三分类 + U矩阵 + 行重排/翻转判别实验。
验证假说：μ 正偏置 = (LLL行负主导) × (GSO向量负主导) 的负负得正。
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
            elif mode == 'flip':
                val = row[r]
                if k >= i:
                    val = -val   # 负号规则翻转（上三角取负）
            A[i, k] = val
    return A

def build_B0(row, mode, shuffle_A=False):
    d = len(row)
    A = build_A(row, mode)
    if shuffle_A:
        perm = np.random.default_rng(12345 + len(row)).permutation(d)
        A = A[perm]
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

def lll_with_U(B0):
    n = B0.shape[0]
    M = IntegerMatrix(n, n)
    for i in range(n):
        for j in range(n):
            M[i, j] = int(B0[i, j])
    U = IntegerMatrix(n, n)
    LLL.reduction(M, U)
    B = np.array([[M[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    Ua = np.array([[U[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    return B, Ua

def sign3(X):
    pos = (X > 0).mean()
    neg = (X < 0).mean()
    zer = (X == 0).mean()
    return pos, neg, zer

def dc1_pos(mu, n):
    idx = np.tril_indices(n, -1)
    iu, ju = idx
    dc = np.minimum(np.abs(iu - ju), n - np.abs(iu - ju))
    m = dc == 1
    absv = np.abs(mu[iu[m], ju[m]])
    nz = absv > 1e-12
    pos = mu[iu[m], ju[m]] > 1e-12
    if nz.sum() == 0:
        return 0.5, 0
    return float(pos[nz].mean()), int(nz.sum())

def run(seed, mode, d, shuffle=False):
    rng = np.random.default_rng(seed)
    row = rng.integers(0, Q, d)
    B0, A = build_B0(row, mode, shuffle)
    n = 2 * d
    B, Ua = lll_with_U(B0)
    # 验证 U·B0 == B（取前两行抽查）
    sig, mu, bs = gso_mu(B)
    pp, nn = dc1_pos(mu, n)
    pb_pos, pb_neg, pb_zer = sign3(B)
    ps_pos, ps_neg, ps_zer = sign3(bs)
    # 符号模型预测：P(<b_i,b*_j>>0) ~ P(b<0)P(b*<0)+P(b>0)P(b*>0)（独立、零贡献忽略）
    p_pred = pb_neg * ps_neg + pb_pos * ps_pos
    # U 矩阵：qI 列权重占比（输出行在输入 qI 行上的展开权重）
    qw = np.abs(Ua[:, d:]).sum() / (np.abs(Ua).sum() + 1e-30)
    # U 行稀疏性
    nzU = (Ua != 0).mean()
    return dict(seed=seed, mode=mode, d=d, shuffle=shuffle,
                Pp=pp, Nnz=nn, p_pred=p_pred,
                pb=(pb_pos, pb_neg, pb_zer), ps=(ps_pos, ps_neg, ps_zer),
                qw=qw, nzU=nzU)

if __name__ == '__main__':
    seeds = [1, 2, 3, 4, 5, 6, 7, 8]
    for mode in ['real', 'mod', 'cent', 'flip']:
        for seed in seeds:
            r = run(seed, mode, 64)
            print(json.dumps(r)); sys.stdout.flush()
    # 行重排（real-shuffle）
    for seed in seeds:
        r = run(seed, 'real', 64, shuffle=True)
        r['mode'] = 'real_shuf'
        print(json.dumps(r)); sys.stdout.flush()
    # d=128 REAL
    for seed in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        r = run(seed, 'real', 128)
        print(json.dumps(r)); sys.stdout.flush()
