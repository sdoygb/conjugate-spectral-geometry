"""块分解诊断：μ 矩阵的块对角结构（对 0.9.6.03 严格化的结构锚点）。
按 LLL 输出序分块：块 I(qI×qI) / 交叉块(A×qI) / 块 II(A×A)。
验证：
 1) 块 I Σμ² ≈ 0 精确（qI 行 GSO 正交）；
 2) 交叉块稀疏：值 ∈ {m/q}（m 小整数），每 A 行至多 1 个匹配非零；
 3) 块 II 主导：Σμ² 与 λ_max 几乎全部来自 A-A 块；
 4) λ_max(MMᵀ) ≈ λ_max(M_AA·M_AAᵀ)；
 5) A 区输出序与输入序的置换度（Kendall tau）；
 6) 匹配对（k_j = k_i - d）的 QA/AQ 分裂。
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

def kendall_tau(x):
    """x 是置换（0..len-1 的排列），返回与恒等序的 Kendall tau。"""
    n = len(x)
    inv = 0
    for i in range(n):
        for j in range(i + 1, n):
            if x[i] > x[j]:
                inv += 1
    return 1.0 - 4.0 * inv / (n * (n - 1))

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
    kmain = np.argmax(np.abs(U), axis=1)
    tmain = (kmain >= d).astype(int)
    qpos = np.where(tmain == 1)[0]
    apos = np.where(tmain == 0)[0]
    tri = np.tril(np.ones((n, n), dtype=bool), -1)
    s2 = mu ** 2
    # 块 I（qI×qI）
    maskI = tri & (tmain[:, None] == 1) & (tmain[None, :] == 1)
    sI = float(s2[maskI].sum())
    # 交叉块
    maskC = tri & (tmain[:, None] != tmain[None, :])
    cvals = mu[maskC]
    cnz = np.abs(cvals) > 1e-12
    sC = float(s2[maskC].sum())
    c_q = cvals[cnz] * Q                       # 值 × q，应接近整数
    c_int_ok = bool(np.all(np.abs(c_q - np.round(c_q)) < 1e-6)) if len(c_q) else True
    # 每 A 行交叉非零数（行位置 i ∈ apos，列 j < i 任意）
    row_nz = {}
    for i in apos:
        r = mu[i, :i]
        row_nz[int(i)] = int((np.abs(r) > 1e-12).sum())
    rnz = np.array(list(row_nz.values()))
    # 匹配对统计：A 行 k_j 与 qI 列 k_i = k_j + d
    #   A 行 k_j 在输出位置 iA；qI 列 k_j+d 的行在输出位置 iQ（若存在）
    match_QA = match_AQ = 0
    match_mu = []
    for j in apos:
        kj = int(kmain[j])                     # A 行号
        qcol = kj + d                          # 匹配的 qI 列
        cand = np.where(kmain == qcol)[0]      # 该 qI 列的行在输出位置
        if len(cand):
            iQ = int(cand[0])
            if iQ < j:                         # qI 在前 → QA 型
                match_QA += 1
                match_mu.append(float(mu[j, iQ]))
            else:                              # A 在前 → AQ 型
                match_AQ += 1
                match_mu.append(float(mu[iQ, j]))
    # 块 II（A×A）
    maskII = tri & (tmain[:, None] == 0) & (tmain[None, :] == 0)
    sII = float(s2[maskII].sum())
    tot = float(s2[tri].sum())
    # λ_max 对比
    M = mu.copy()
    lam_max_full = float(np.linalg.eigvalsh(M @ M.T)[-1])
    if len(apos) >= 2:
        MAA = mu[np.ix_(apos, apos)]
        lam_max_AA = float(np.linalg.eigvalsh(MAA @ MAA.T)[-1])
    else:
        lam_max_AA = -1.0
    # A 区置换度：kmain[apos] 的顺序（按位置排序后）与恒等序的 Kendall tau
    order_a = kmain[apos]
    tau = kendall_tau(list(order_a))
    return dict(seed=seed, mode=mode, shuffle=shuffle, d=d, u_ok=bool(u_ok),
                sI=sI, sC=sC, sII=sII, s_tot=tot,
                cross_nz=int(cnz.sum()), cross_cnt=int(maskC.sum()),
                cross_nz_rate=float(cnz.mean()),
                cross_int_ok=c_int_ok,
                cross_q_min=float(c_q.min()) if len(c_q) else 0.0,
                cross_q_max=float(c_q.max()) if len(c_q) else 0.0,
                row_nz_max=int(rnz.max()) if len(rnz) else 0,
                row_nz_med=float(np.median(rnz)) if len(rnz) else 0.0,
                match_QA=match_QA, match_AQ=match_AQ,
                match_mu_min=float(np.min(np.abs(match_mu))) if match_mu else -1.0,
                match_mu_max=float(np.max(np.abs(match_mu))) if match_mu else -1.0,
                lam_max_full=lam_max_full, lam_max_AA=lam_max_AA,
                kendall_tau=float(tau),
                n_qI=len(qpos), n_A=len(apos))

if __name__ == '__main__':
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    seeds = [1, 2, 3, 4, 5, 6, 7, 8]
    for mode in ['real', 'cent', 'mod']:
        for seed in seeds:
            r = run(seed, mode, d=d)
            print(json.dumps(r)); sys.stdout.flush()
    for seed in seeds:
        r = run(seed, 'real', shuffle=True, d=d)
        print(json.dumps(r)); sys.stdout.flush()
