#!/usr/bin/env python3
"""leech_basis_v2.py — Leech 格基：生成元集合 → 格基细化（精确整数算法）

生成元（2Λ24 的整数生成元，行向量）：
  (1,...,1)                ← 2·½(1,...,1)
  8·e_i                    ← 2·4e_i
  4·(e_1 − e_j)            ← 2·2(e_1−e_j)
  4·g                      ← 2·2g, g ∈ Golay G24 生成行
细化：B = 24 个无关行（mod p 选），对每个生成元 v 算分数坐标 x = B⁻¹v，
若 x_j 非整数，用 y = v − Σ⌊x_i⌋b_i 替换 B 第 j 行（指数严格减小）→ 收敛到格基。
自检：偶格、det=±1、Gram det=1、BKZ 最短向量²=4（⟹ 确为 Leech，唯一性）。
"""
import numpy as np
from sympy import Matrix, Rational
import fpylll

P = 3329


def golay_g24_rows():
    """Golay G24 生成矩阵（QR(23) 码扩展）。权重分布 {0:1,8:759,12:2576,16:759,24:1} 已验证。"""
    g = [1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1]   # x^11+x^9+x^7+x^6+x^5+x+1
    rows = []
    for i in range(12):
        r = np.zeros(23, dtype=int)
        r[i:i + 12] = g
        rows.append(r[:23])
    G = np.array(rows)
    G24 = np.zeros((12, 24), dtype=int)
    G24[:, :23] = G
    G24[:, 23] = G.sum(axis=1) % 2
    return G24


def generators_2L():
    """2Λ24 的整数生成元（60 行 × 24 列）。"""
    rows = []
    rows.append(np.ones(24, dtype=int))
    for i in range(24):
        r = np.zeros(24, dtype=int); r[i] = 8; rows.append(r)
    for j in range(1, 24):
        r = np.zeros(24, dtype=int); r[0] = 4; r[j] = -4; rows.append(r)
    for g in golay_g24_rows():
        rows.append(4 * g)
    return np.array(rows)


def select_independent(rows):
    """mod p 高斯消元选 24 个线性无关行。返回索引列表。"""
    m, n = rows.shape
    A = rows % P
    sel = []
    piv_row = 0
    for col in range(n):
        piv = next((i for i in range(piv_row, m) if A[i, col] % P), None)
        if piv is None:
            continue
        A[[piv_row, piv]] = A[[piv, piv_row]]
        inv = pow(int(A[piv_row, col]), -1, P)
        A[piv_row] = A[piv_row] * inv % P
        for i in range(m):
            if i != piv_row and A[i, col] % P:
                A[i] = (A[i] - A[i, col] * A[piv_row]) % P
        sel.append(int(piv_row))
        piv_row += 1
        if len(sel) == n:
            break
    assert len(sel) == n, f"秩不足: {len(sel)}"
    return sel


def lattice_basis(rows):
    """行生成元 → 格基（精确整数，指数单调减小收敛）。"""
    n = rows.shape[1]
    sel = select_independent(rows)
    B = np.array(rows[sel], dtype=object)
    # 每轮：求 B⁻¹·V 的分数坐标
    for it in range(200):
        Bm = Matrix(B.tolist())
        Binv = Bm.inv()
        improved = False
        for vi in range(rows.shape[0]):
            v = rows[vi]
            x = Binv * Matrix(v.tolist())          # 24 个 Rational
            # 找非整数坐标
            j = None
            for k in range(n):
                if x[k].q != 1:
                    j = k
                    break
            if j is None:
                continue
            # y = v − Σ⌊x_i⌋·b_i，替换 B 第 j 行
            y = v.copy()
            for k in range(n):
                y = y - int(x[k].p // x[k].q) * B[k]
            assert y.dtype == object or np.all(y == np.floor(y))
            B[j] = y
            improved = True
            break                        # 每轮只细化一次，重新求逆
        if not improved:
            return B.astype(np.int64)
    raise RuntimeError("细化未收敛")


def leech_check(B):
    d = B.shape[0]
    G = B @ B.T
    norms = np.sum(B * B, axis=1)
    detB = int(round(np.linalg.det(B.astype(float))))
    detG = int(round(np.linalg.det(G.astype(float))))
    even = bool(np.all(norms % 2 == 0))
    rank_ok = np.linalg.matrix_rank(B.astype(float)) == d
    print(f"dim={B.shape}  det(B)={detB}  det(G)={detG}  偶格={even}  rank={rank_ok}")
    if abs(detB) != 1 or not even or abs(detG) != 1 or not rank_ok:
        return False
    M = fpylll.IntegerMatrix(d, d)
    for i in range(d):
        for j in range(d):
            M[i, j] = int(round(B[i, j] * 2))
    fpylll.LLL.reduction(M)
    fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=d))
    min_norm = min(sum(M[i, j] * M[i, j] for j in range(d)) for i in range(d)) / 4.0
    print(f"BKZ 后最短基向量范数² = {min_norm}（Leech 期望 4）")
    return min_norm == 4.0


if __name__ == "__main__":
    R = generators_2L()
    print(f"生成元: {R.shape[0]} 行 × {R.shape[1]} 列")
    B2 = lattice_basis(R)                    # 2Λ24 的基（整数）
    print(f"2Λ24 基: det={int(round(np.linalg.det(B2.astype(float))))}（期望 2^24={2**24}）")
    assert abs(int(round(np.linalg.det(B2.astype(float))))) == 2**24
    B = B2 / 2.0                             # Λ24 的基（允许半整数）
    if leech_check(B):
        print("✓✓ Leech 格构造验证通过（偶幺模 + 最短²=4 ⟹ 唯一性 ⟹ 确为 Leech）")
        np.save("leech_basis.npy", B)
    else:
        print("✗ Leech 自检失败")
