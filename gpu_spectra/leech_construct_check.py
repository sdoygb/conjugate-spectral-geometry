#!/usr/bin/env python3
"""leech_construct_check.py — Leech 格构造验证（第一性原理）

Golay G24 构造：G23 = QR(23) 循环码（生成多项式 g(x)）→ parity 扩展。
自检：枚举 2^12 码字，权重分布必须为 [24,12,8]（A_8=759）。
Leech 基（C-S SPLAG §10.4 风格）：
  行 1       : 8·e_1
  行 2..13   : 4·(e_1 + e_j),  j=2..13
  行 14..24  : 2·(Golay 码字), 11 个（含全 1 码字 → 全 2 行）
自检：det=±1（整数精确）、偶格、Gram det=1、BKZ 最短向量²=4。
"""
import numpy as np
import fpylll


def poly_shift_register(g, n=23):
    """循环码生成矩阵：g(x), x·g(x), ..., x^{k-1}·g(x)，长度 n。g 为低次在前系数。"""
    k = len(g)
    rows = []
    for i in range(k):
        r = np.zeros(n, dtype=int)
        r[i:i + k] = g
        # 循环码：x^i·g(x) mod (x^n - 1)；若超出长度则回卷（G23 是循环码，g | x^23+1 时自动）
        r = np.roll(r, 0)
        rows.append(r[:n])
    return np.array(rows)


def golay_g23(g_coeff):
    """G23 生成矩阵（23 列，12 行，循环码）+ 自检最小距离。"""
    k = len(g_coeff)
    rows = []
    for i in range(k):
        r = np.zeros(23, dtype=int)
        r[i:i + k] = g_coeff
        rows.append(r[:23])
    G = np.array(rows)
    # 最小距离：枚举 2^12
    dmin = 23
    for mask in range(1, 1 << k):
        c = np.zeros(23, dtype=int)
        for i in range(k):
            if mask >> i & 1:
                c ^= G[i]
        dmin = min(dmin, int(c.sum()))
    return G, dmin


def golay_g24_from_g23(g_coeff):
    """G24 = G23 + parity 位。自检权重分布（min=8, A_8=759）。"""
    G23, d23 = golay_g23(g_coeff)
    k = G23.shape[0]
    G24 = np.zeros((k, 24), dtype=int)
    G24[:, :23] = G23
    G24[:, 23] = G23.sum(axis=1) % 2
    # 权重分布
    hist = {}
    for mask in range(1 << k):
        c = np.zeros(24, dtype=int)
        for i in range(k):
            if mask >> i & 1:
                c ^= G24[i]
        w = int(c.sum())
        hist[w] = hist.get(w, 0) + 1
    ok = (hist.get(0, 0) == 1 and hist.get(8, 0) == 759 and hist.get(12, 0) == 2576
          and hist.get(16, 0) == 759 and hist.get(24, 0) == 1 and hist.get(4, 0) == 0)
    return G24, hist, ok


def leech_basis(g24_rows):
    """由 Golay 生成行构造 Leech 24×24 基。g24_rows：12 行 [24,12,8] 生成矩阵。
    取 11 行：其中必须能凑出全 1 码字（用全 1 行替换第 0 行避免 rank 缺失）。
    """
    rows = []
    r = np.zeros(24); r[0] = 8.0; rows.append(r)          # 8e_1
    for j in range(1, 13):                                 # 4(e_1 + e_j), j=2..13 (0-indexed 1..12)
        r = np.zeros(24); r[0] = 4.0; r[j] = 4.0; rows.append(r)
    # 11 个 2·码字：全 1 码字 + 10 个 Golay 生成行
    rows.append(np.full(24, 2.0))                          # 2·(1,...,1)
    for i in range(1, 11):                                 # 10 个生成行（跳过行 0）
        rows.append(2.0 * g24_rows[i])
    return np.array(rows)


def leech_check(B):
    d = B.shape[0]
    G = B @ B.T
    norms = np.sum(B * B, axis=1)
    detB = round(np.linalg.det(B))
    detG = round(np.linalg.det(G))
    even = bool(np.all(norms % 2 == 0))
    rank_ok = np.linalg.matrix_rank(B) == d
    print(f"dim={B.shape}  det(B)={detB}  det(G)={detG}  偶格={even}  rank={rank_ok}")
    if abs(detB) != 1 or not even or abs(detG) != 1 or not rank_ok:
        return False
    # BKZ 最短向量
    M = fpylll.IntegerMatrix(d, d)
    for i in range(d):
        for j in range(d):
            M[i, j] = int(round(B[i, j]))
    fpylll.LLL.reduction(M)
    fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=d))
    min_norm = min(sum(M[i, j] * M[i, j] for j in range(d)) for i in range(d))
    print(f"BKZ 后最短基向量范数² = {min_norm}（Leech 期望 4）")
    return min_norm == 4


if __name__ == "__main__":
    # 候选生成多项式（G23 的两种可能因子）
    candidates = {
        "g1: x^11+x^9+x^7+x^6+x^5+x+1": [1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1],
        "g2: x^11+x^10+x^6+x^5+x^4+x^2+1": [1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1],
    }
    for name, g in candidates.items():
        G24, hist, ok = golay_g24_from_g23(g)
        print(f"--- {name}")
        print(f"  G24 权重分布: {dict(sorted(hist.items()))}  [24,12,8]? {ok}")
        if ok:
            print("  → 确为 Golay G24，构造 Leech 基...")
            B = leech_basis(G24)
            if leech_check(B):
                print("  ✓✓ Leech 格构造验证通过（偶幺模 + 最短²=4 ⟹ 唯一性 ⟹ 确为 Leech）")
                np.save("/tmp/leech_basis.npy", B)
            else:
                print("  ✗ Leech 自检失败")
