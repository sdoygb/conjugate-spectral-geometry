"""诊断：对径消失机制 + 负分量位置聚集 + qI/A 输出序结构。
d=64, N=8, modes: real/cent/mod + shuffle(real 行重排对照)。
输出：U 变换矩阵验证、输出序 qI/A 位置、对径对类型分解、负分量位置。
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

def lll_with_U(B0):
    n = B0.shape[0]
    M = IntegerMatrix(n, n)
    U = IntegerMatrix(n, n)
    for i in range(n):
        U[i, i] = 1
        for j in range(n):
            M[i, j] = int(B0[i, j])
    LLL.reduction(M, U)
    B = np.array([[M[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    Ua = np.array([[U[i, j] for j in range(n)] for i in range(n)], dtype=np.int64)
    return B, Ua

def run(seed, mode, shuffle=False, d=64):
    rng = np.random.default_rng(seed)
    row = rng.integers(0, Q, d)
    B0, A = build_B0(row, mode)
    if shuffle:
        perm = rng.permutation(d)
        B0s = B0.copy()
        B0s[:d] = B0[perm]
        B0 = B0s
    n = 2 * d
    B, U = lll_with_U(B0)
    u_ok = np.array_equal(U @ B0, B)
    sig, mu, bs = gso_mu(B)
    # 主导输入行（U 行绝对值 argmax）
    kmain = np.argmax(np.abs(U), axis=1)
    tmain = (kmain >= d).astype(int)          # 0=A 块, 1=qI 块
    # 1) 输出序：qI 行在输出中的位置（min/med/max）+ 前 d 行中 qI 占比
    qi_pos = np.where(tmain == 1)[0]
    a_pos = np.where(tmain == 0)[0]
    order = dict(
        qi_min=int(qi_pos.min()) if len(qi_pos) else -1,
        qi_med=float(np.median(qi_pos)) if len(qi_pos) else -1,
        qi_max=int(qi_pos.max()) if len(qi_pos) else -1,
        qi_frac_first_half=float((qi_pos < d).mean()) if len(qi_pos) else -1,
        a_min=int(a_pos.min()) if len(a_pos) else -1,
        a_med=float(np.median(a_pos)) if len(a_pos) else -1,
        a_max=int(a_pos.max()) if len(a_pos) else -1,
    )
    # 2) 对径对 (i, i+d) 的类型分解
    antip = {}
    for key in ['AA', 'AQ', 'QA', 'QQ']:
        antip[key] = [0, 0.0, 0, 0]   # cnt, sum|mu|, nz, pos&nz
    dk = []
    for i in range(d):
        j = i + d
        key = ('A' if tmain[i] == 0 else 'Q') + ('A' if tmain[j] == 0 else 'Q')
        v = abs(mu[j, i]); nz = v > 1e-12; pos = mu[j, i] > 1e-12
        antip[key][0] += 1; antip[key][1] += v; antip[key][2] += int(nz); antip[key][3] += int(pos and nz)
        dk.append(abs(int(kmain[j]) - int(kmain[i])))
    dk = np.array(dk)
    # 3) 负分量位置聚集：每行 i，负/正 μ 的归一化列位置 j/i
    neg_pos_list, pos_pos_list = [], []
    for i in range(1, n):
        r = mu[i, :i]
        ng = np.where(r < -1e-12)[0]
        ps = np.where(r > 1e-12)[0]
        if len(ng):
            neg_pos_list.append(float(ng.mean() / i))
        if len(ps):
            pos_pos_list.append(float(ps.mean() / i))
    neg_pos = float(np.mean(neg_pos_list)) if neg_pos_list else -1.0
    pos_pos = float(np.mean(pos_pos_list)) if pos_pos_list else -1.0
    # 4) 对径 μ 的分子分解（前 3 个对径对的坐标贡献）
    decomp = []
    for i in range(min(3, d)):
        j = i + d
        num = B[j].astype(np.float64) @ bs[i]
        decomp.append(dict(i=int(i), ki=int(kmain[i]), kj=int(kmain[j]),
                           num=float(num), sig_i=float(sig[i]), mu_ji=float(mu[j, i])))
    return dict(seed=seed, mode=mode, shuffle=shuffle, u_ok=bool(u_ok),
                order=order, antip=antip,
                dk=dict(min=int(dk.min()), med=float(np.median(dk)),
                        max=int(dk.max()), mean=float(dk.mean())),
                neg_pos=neg_pos, pos_pos=pos_pos,
                decomp=decomp,
                sig_first10=[float(x) for x in sig[:10]])

if __name__ == '__main__':
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    seeds = [1, 2, 3, 4, 5, 6, 7, 8]
    for mode in ['real', 'cent', 'mod']:
        for seed in seeds:
            r = run(seed, mode, d=d)
            print(json.dumps(r)); sys.stdout.flush()
    # shuffle 对照（real 的 A 行重排）
    for seed in seeds:
        r = run(seed, 'real', shuffle=True, d=d)
        print(json.dumps(r)); sys.stdout.flush()
