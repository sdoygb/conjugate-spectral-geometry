#!/usr/bin/env python3
"""highsym_spectra.py — 里程碑 B：高对称格的谱刚性（Λ_H 指纹与随机基系综）
项目：格谱统计工具箱 (Lattice Spectral Statistics on GPU)
文章 0.9（260821）定理 0.9.4.01/02/10/11；猜想 10.75（260823）三尺度统计刚性——群尺度部分

问题（10.75 群尺度预言）：
  对称性越高的格，其统计量（谱刚性比 Λ_H = λ₂/λ₁ of G=BBᵀ）越刚性。
  检验：① 规范基单样本指纹（高对称格 vs 随机格）；② 随机约化基系综的 Λ_H 方差。

格族（自同构群 |Aut| 从大到小）：
  Leech Λ24 : |Aut| = 8.3e18（Conway 群 Co₀）     ← 待自检构造
  E₈        : |W(E₈)| = 696,729,600
  D_d       : |W(D_d)| = 2^{d-1}·d!
  A_d       : |W(A_d)| = (d+1)!
  Z^d       : |Aut| = GL_d(Z)（无限，平凡对称）
  随机格     : 无对称（对照）

用法：
  python3 highsym_spectra.py fingerprint   # 单样本指纹表
  python3 highsym_spectra.py ensemble N    # 随机基系综（默认 N=2000）
  python3 highsym_spectra.py leech-check   # Leech 候选自检（det/偶格/最短向量）
"""
import sys
import time

import numpy as np
import fpylll

Q = 3329


# ---------------------------------------------------------------- 格基构造

def z_basis(d):
    """Z^d：单位基"""
    return np.eye(d, dtype=np.float64)


def d_basis(d):
    """D_d：{e_i−e_{i+1}, i=1..d−1} ∪ {e_{d−1}+e_d}（det=±2）"""
    B = np.zeros((d, d))
    for i in range(d - 1):
        B[i, i] = 1.0
        B[i, i + 1] = -1.0
    B[d - 1, d - 2] = 1.0
    B[d - 1, d - 1] = 1.0
    return B


def a_basis(d):
    """A_d：根 e_i−e_{i+1}, i=1..d，嵌入 Z^{d+1}（B 是 d×(d+1)，Gram 是 Cartan A_d）"""
    B = np.zeros((d, d + 1))
    for i in range(d):
        B[i, i] = 1.0
        B[i, i + 1] = -1.0
    return B


def e8_basis():
    """E₈（偶幺模格，det=±1）构造：D₈ 基 ∪ ½(1,...,1) 平移类 → ×2 整数化 → HNF → ÷2。
    8 维偶幺模格唯一 ⟹ 该格即 E₈。自检：det(2E₈ 基)=2⁸、Gram det=1、行范数² 全偶。"""
    rows = []
    for i in range(7):
        r = np.zeros(8); r[i] = 1.0; r[i + 1] = -1.0; rows.append(r)
    r = np.zeros(8); r[6] = 1.0; r[7] = 1.0; rows.append(r)   # e₇+e₈（补全 D₈）
    r = np.full(8, 0.5); rows.append(r)                       # ½(1,...,1)（平移类）
    M = np.array(rows) * 2                                    # 2E₈ 生成元（整数）
    H = _hnf_gcd(M.astype(object))
    if H.shape[0] != 8:
        raise ValueError(f"E8 HNF 秩 {H.shape[0]} ≠ 8")
    import sympy as sp
    detH = abs(int(sp.Matrix(H.tolist()).det()))
    if detH != 2 ** 8:
        raise ValueError(f"det(2E8 基) = {detH} ≠ 2⁸，构造失败")
    return H.astype(np.float64) / 2


# ---- Leech 格构造（验证器 + HNF，可靠性优先）----
# 定义（Wikipedia/SPLAG）：Λ₂₄ = 2^{-1/2}·{ x ∈ Z²⁴ : Σxᵢ ≡ 4m (mod 8)，
#   且 S_m(x) := {i : xᵢ ≡ m (mod 4)} ∈ C(Golay) }，m ∈ {0,1}。
# √2·Λ₂₄ 是 Z²⁴ 的子格（det = 2²⁴，最小范数² = 8）。
# 构造流程：生成候选格点 → 验证器过滤 → HNF 取基 → 三重自检（det/验证/最短向量）。
def _golay_generator():
    """Golay G24 生成矩阵 [I_12|P]（Paley 构造，程序搜索验证唯一）：
    P[i][j] = 1 若 i=j（对角），或 (i−j) mod 11 ∈ QR(11)（i,j≥1）；
    ∞ 行/列（索引 0）全 1，∞ 对角 = 0。
    自检（_check_golay）：自正交 + 秩 12 + 最小权重 8 ⟹ 唯一 [24,12,8] 码。"""
    S = {1, 3, 4, 5, 9}          # 模 11 二次剩余
    P = np.zeros((12, 12), dtype=int)
    for i in range(1, 12):
        for j in range(1, 12):
            if i == j:
                P[i, j] = 1
            elif (i - j) % 11 in S:
                P[i, j] = 1
    P[0, 1:] = 1
    P[1:, 0] = 1
    return np.hstack([np.eye(12, dtype=int), P])


def _check_golay(G):
    """G24 自检：自正交（两两内积 mod 2 = 0）、秩 12、全 1 ∈ 码、最小权重 8"""
    for i in range(12):
        for j in range(i, 12):
            if int((G[i] @ G[j]) % 2) != 0:
                return False
    if np.linalg.matrix_rank(G.T % 2) != 12:
        return False
    one = np.ones(24, dtype=int)
    if not _in_code(one, G % 2):
        return False
    minw = 99
    for m in range(1, 4096):
        v = np.zeros(24, dtype=int)
        for i in range(12):
            if (m >> i) & 1:
                v = (v + G[i]) % 2
        minw = min(minw, int(v.sum()))
    return minw == 8


def leech_golay_check():
    G = _golay_generator()
    ok = _check_golay(G)
    if not ok:
        return None
    return G


def leech_basis():
    """√2·Λ₂₄ 的 24×24 整数基（HNF），自检后返回（格点坐标为 float64）。
    若自检失败抛 ValueError。"""
    G = leech_golay_check()
    if G is None:
        raise ValueError("Golay G24 生成矩阵自检失败")
    C = G % 2
    # 候选格点（C24' = {x ∈ Z²⁴ : x mod 2 ∈ G24, Σx ≡ 0 mod 4} = √2Λ₂₄ 的等价描述）：
    #   4eᵢ（24，生成 4Z²⁴）；2cᵢ（12，偶坐标码字）；1_{supp cᵢ}（12，奇坐标码字支撑）
    cands = []
    for i in range(24):
        r = np.zeros(24, dtype=int); r[i] = 4; cands.append(r)
    for i in range(12):
        cands.append(2 * C[i])
    for i in range(12):
        s = np.zeros(24, dtype=int)
        s[C[i] == 1] = 1
        cands.append(s)
    # 验证器过滤
    ok = []
    for r in cands:
        if _in_c24prime(r, C):
            ok.append(r)
    # HNF（整数行阶梯：gcd 列主元消元，主元行张成同一格）
    M = np.array(ok, dtype=object)
    H = _hnf_gcd(M)
    basis = H[H.any(axis=1).astype(bool)]
    if basis.shape[0] != 24:
        raise ValueError(f"HNF 秩 {basis.shape[0]} ≠ 24")
    B = basis.astype(np.float64)
    # 自检 1：det = ±2²⁴（sympy 精确整数行列式）
    import sympy as sp
    det = abs(int(sp.Matrix(basis.tolist()).det()))
    if det != 2 ** 24:
        raise ValueError(f"det(B) = {det} ≠ 2²⁴，构造失败")
    # 自检 2：所有基行通过验证器
    if not all(_in_c24prime(row, C) for row in basis):
        raise ValueError("基行未通过 Leech 验证器")
    # 自检 3：最短向量² = 8（BKZ）
    min_norm = _min_vector_norm2(B)
    if min_norm != 8:
        raise ValueError(f"最短向量范数² = {min_norm} ≠ 8")
    return B


def _in_c24prime(x, C):
    """C24' 验证器：x mod 2 ∈ span(C)（Golay 码空间）且 Σx ≡ 0 (mod 4)"""
    x = np.asarray(x, dtype=int)
    v = (x % 2).astype(int)
    if not _in_code(v, C):
        return False
    return int(x.sum()) % 4 == 0


def _in_code(v, C):
    """v ∈ span(C) mod 2？精确整数高斯消元"""
    return _solve_gf2(C.T % 2, np.asarray(v, dtype=int) % 2)


def _solve_gf2(A, b):
    """A z = b (mod 2) 是否有解？精确高斯消元（增广矩阵行阶梯）"""
    aug = np.hstack([A.copy() % 2, b.reshape(-1, 1) % 2]).astype(int)
    m, n = aug.shape
    r = 0
    for col in range(n - 1):
        piv = None
        for row in range(r, m):
            if aug[row, col] % 2 == 1:
                piv = row
                break
        if piv is None:
            continue
        aug[[r, piv]] = aug[[piv, r]]
        for row in range(m):
            if row != r and aug[row, col] % 2 == 1:
                aug[row] = (aug[row] + aug[r]) % 2
        r += 1
        if r == m:
            break
    return all(aug[row, -1] % 2 == 0 for row in range(r, m))


def _hnf_gcd(M):
    """整数行阶梯（Hermite 标准形，列主元 + 带余消元）。M: (k,n) int → 主元行列表。
    每列选绝对值最小非零行为主元，带余除法消去其余行，主元行移出。
    全部行操作整数可逆 ⟹ 主元行与原始生成元张成同一格。"""
    M = M.astype(object).copy()
    k, n = M.shape
    keep = []
    for col in range(n):
        while True:
            nz = [r for r in range(k) if M[r, col] != 0]
            if not nz:
                break
            piv = min(nz, key=lambda r: abs(M[r, col]))
            if M[piv, col] < 0:
                M[piv] = -M[piv]
            pv = M[piv, col]
            stable = True
            for r in range(k):
                if r != piv and M[r, col] != 0:
                    q = M[r, col] // pv
                    M[r] = M[r] - q * M[piv]
                    if M[r, col] != 0:
                        stable = False
            if stable:
                break
        nz = [r for r in range(k) if M[r, col] != 0]
        if not nz:
            continue
        piv = min(nz, key=lambda r: abs(M[r, col]))
        keep.append(M[piv].copy())
        M = np.delete(M, piv, axis=0)
        k -= 1
        if k == 0:
            break
    return np.array(keep)


def _min_vector_norm2(B):
    """最短非零向量范数²：BKZ 深缩短后取最小行范数²（对幺模 det 格足够）"""
    M = fpylll.IntegerMatrix(24, 24)
    for i in range(24):
        for j in range(24):
            M[i, j] = int(round(B[i, j]))
    fpylll.LLL.reduction(M)
    fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=24))
    return min(sum(M[i, j] * M[i, j] for j in range(24)) for i in range(24))


# ---------------------------------------------------------------- Λ_H 工具

def lambda_H(B):
    """Λ_H = λ₂/λ₁ of G = BBᵀ（最小两特征值比）"""
    G = B @ B.T
    ev = np.linalg.eigvalsh(G)
    return ev[1] / ev[0]


def lambda_H_eigs(B):
    G = B @ B.T
    ev = np.linalg.eigvalsh(G)
    return ev[0], ev[1]


def gram_checks(B):
    """格自检：B 行范数² 偶性（偶格）、Gram det、满秩（A_d 嵌入非方阵时跳过 det(B)）"""
    G = B @ B.T
    norms = np.sum(B * B, axis=1)
    sq = B.shape[0] == B.shape[1]
    return dict(
        det=float(np.linalg.det(B)) if sq else float("nan"),
        gram_det=float(np.linalg.det(G)),
        even=bool(np.all(np.round(norms) % 2 == 0)),
        full_rank=bool(np.linalg.matrix_rank(B) == B.shape[0]),
        dim=B.shape,
    )


# ---------------------------------------------------------------- 随机基系综

def random_basis(d, seed=7):
    """一般随机格基（对照，无对称性）：系数均匀于 {−3..3} 的随机整数方阵（Gram 正定）"""
    rng = np.random.default_rng(seed)
    return rng.integers(-3, 4, size=(d, d)).astype(np.float64)


def random_unimodular(d, nsteps=40, rng=None):
    """随机幺模变换 U = ∏ E_{ij}(±1)（det=±1）。U ∈ GL_d(Z)。"""
    if rng is None:
        rng = np.random.default_rng(11)
    U = np.eye(d, dtype=np.int64)
    for _ in range(nsteps):
        i, j = rng.integers(0, d, size=2)
        while j == i:
            j = rng.integers(0, d)
        s = rng.choice([-1, 1])
        E = np.eye(d, dtype=np.int64)
        E[i, j] = s
        U = E @ U
    return U


def lll_reduce(B, delta=0.99):
    """LLL 约化（fpylll，整数矩阵）。返回约化基（float64）。"""
    d = B.shape[0]
    M = fpylll.IntegerMatrix(d, d)
    for i in range(d):
        for j in range(d):
            M[i, j] = int(round(B[i, j]))
    fpylll.LLL.reduction(M, delta=delta)
    R = np.zeros((d, d), dtype=np.float64)
    for i in range(d):
        for j in range(d):
            R[i, j] = float(M[i, j])
    return R


def ensemble(B, N=2000, nsteps=40, use_lll=True, seed=20260823):
    """随机约化基系综：B·U（U 随机幺模）→ LLL → Λ_H 分布。
    返回 (lam (N,), dict)。B 应为整数矩阵（或半整数×2 的整数化）。"""
    rng = np.random.default_rng(seed)
    d = B.shape[0]
    lam = np.empty(N)
    lam_red = np.empty(N)          # 未经 LLL 的原始 BU 的 Λ_H（对照）
    t0 = time.perf_counter()
    for t in range(N):
        U = random_unimodular(d, nsteps, rng)
        BU = B @ U
        lam_red[t] = lambda_H(BU)
        if use_lll:
            Bred = lll_reduce(BU)
            lam[t] = lambda_H(Bred)
        else:
            lam[t] = lam_red[t]
    dt = time.perf_counter() - t0
    dev = lam - 1.0
    return lam, dict(
        N=N, seconds=dt, per_sample=dt / N,
        mean=float(lam.mean()), std=float(lam.std()),
        min=float(lam.min()), max=float(lam.max()),
        max_abs_dev=float(np.max(np.abs(dev))),
        std_raw=float(lam_red.std()),
    )


# ---------------------------------------------------------------- 报告

def fingerprint_table():
    """单样本指纹：规范基 Λ_H + 格自检"""
    print("=" * 100)
    print("里程碑 B-1：高对称格规范基的 Λ_H 指纹（定理 0.9.4.01 定义，G=BBᵀ）")
    print("=" * 100)
    print(f"{'格':12s}{'dim':>5s}{'|Aut|':>24s}{'λ₁':>12s}{'λ₂':>12s}{'Λ_H':>12s}{'det B':>10s}{'偶格':>6s}")
    print("-" * 100)
    cases = [
        ("Z^8", z_basis(8), "GL_8(Z) 无限"),
        ("D_8", d_basis(8), "2^7·8! = 5160960"),
        ("A_8", a_basis(8), "9! = 362880"),
        ("E_8", e8_basis(), "696729600"),
        ("Z^24", z_basis(24), "GL_24(Z) 无限"),
        ("随机8", random_basis(8), "平凡（对照）"),
        ("随机24", random_basis(24), "平凡（对照）"),
    ]
    for name, B, aut in cases:
        l1, l2 = lambda_H_eigs(B)
        chk = gram_checks(B)
        print(f"{name:12s}{B.shape[0]:>5d}{aut:>24s}{l1:>12.6e}{l2:>12.6e}"
              f"{l2 / l1:>12.6f}{chk['det']:>10.3f}{'✓' if chk['even'] else '·':>6s}")
    # Leech（√2Λ₂₄ 基，det=2²⁴，最短向量²=8；Λ_H 基无关不变）
    try:
        B = leech_basis()
        chk = gram_checks(B)
        l1, l2 = lambda_H_eigs(B)
        print(f"{'Leech Λ24':12s}{24:>5d}{'8.3e18 (Co₀)':>24s}{l1:>12.6e}{l2:>12.6e}"
              f"{l2 / l1:>12.6f}{chk['det']:>10.3f}{'✓' if chk['even'] else '·':>6s}"
              f"  ✓ det=2²⁴ 最短²=8（√2Λ₂₄）")
    except Exception as e:
        print(f"{'Leech Λ24':12s}{'—':>5s}{'构造异常':>24s}  {e}")
    print("-" * 100)


def ensemble_table(N=2000):
    """随机基系综：Λ_H 分布 vs 对称性梯度"""
    print("=" * 100)
    print(f"里程碑 B-2：随机约化基系综的 Λ_H 统计（N={N}，随机幺模 U→LLL）")
    print("猜想 10.75 群尺度：对称性越高，统计量越刚性（std 越小）")
    print("=" * 100)
    print(f"{'格':12s}{'dim':>5s}{'mean Λ_H':>12s}{'std':>10s}{'min':>12s}{'max':>12s}"
          f"{'max|Λ_H−1|':>12s}{'std(原始BU)':>12s}")
    print("-" * 100)
    B8s = [("Z^8", z_basis(8)), ("D_8", d_basis(8)), ("E_8", e8_basis() * 2),
           ("随机8", random_basis(8))]
    for name, B in B8s:
        lam, st = ensemble(B, N=N)
        print(f"{name:12s}{B.shape[0]:>5d}{st['mean']:>12.6f}{st['std']:>10.3e}"
              f"{st['min']:>12.6f}{st['max']:>12.6f}{st['max_abs_dev']:>12.3e}"
              f"{st['std_raw']:>12.3e}")
    print("-" * 100)
    # 大维度
    B24s = [("Z^24", z_basis(24)), ("随机24", random_basis(24))]
    for name, B in B24s:
        lam, st = ensemble(B, N=max(200, N // 5))
        print(f"{name:12s}{B.shape[0]:>5d}{st['mean']:>12.6f}{st['std']:>10.3e}"
              f"{st['min']:>12.6f}{st['max']:>12.6f}{st['max_abs_dev']:>12.3e}"
              f"{st['std_raw']:>12.3e}")
    # Leech（对称性最高，用较小 N——24 维 LLL 较慢）
    try:
        Bleech = leech_basis()
        lam, st = ensemble(Bleech, N=max(100, N // 10))
        print(f"{'Leech Λ24':12s}{24:>5d}{st['mean']:>12.6f}{st['std']:>10.3e}"
              f"{st['min']:>12.6f}{st['max']:>12.6f}{st['max_abs_dev']:>12.3e}"
              f"{st['std_raw']:>12.3e}")
    except Exception as e:
        print(f"{'Leech Λ24':12s}{'—':>5s}{f'构造异常: {e}':>64s}")
    print("-" * 100)


def leech_check():
    """Leech 构造深度自检（leech_basis 内部已含三重自检）"""
    print("=" * 100)
    print("Leech 格构造自检（√2Λ₂₄ ⊂ Z²⁴：det=2²⁴、验证器、最短向量²=8）")
    print("=" * 100)
    G = _golay_generator()
    print(f"Golay G24 生成矩阵自检: {'✓' if _check_golay(G) else '✗'}")
    try:
        B = leech_basis()
        import sympy as sp
        det = abs(int(sp.Matrix(B.tolist()).det()))
        print(f"[✓] Leech 基构造成功：24×24，det(B)=±{det}")
        l1, l2 = lambda_H_eigs(B)
        print(f"    Λ_H = {l2 / l1:.10f}  (λ₁={l1:.6e}, λ₂={l2:.6e})")
        return True
    except ValueError as e:
        print(f"[✗] {e}")
        return False


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "fingerprint"
    if mode == "fingerprint":
        fingerprint_table()
        return 0
    if mode == "ensemble":
        N = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
        ensemble_table(N)
        return 0
    if mode == "leech-check":
        return 0 if leech_check() else 1
    print(f"未知模式: {mode}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
