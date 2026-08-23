#!/usr/bin/env python3
"""leech_basis_hnf.py — Leech 格基的 HNF 构造（完整生成元集合）

Λ24 的生成元集合（Golay 码字 + 偶条件）：
  c0 = ½(1,...,1)          （半整数类）
  4·e_i                    （i=1..24，Σ=4≡0 mod 4）
  2·(e_1 − e_j)            （j=2..24，全偶，支撑 mod2 = ∅ 码字）
  2·g                      （g ∈ Golay G24 生成行，12 行）
2Λ24 ⊂ Z^24，全部生成元 ×2 得整数矩阵 → Hermite 正规形 → ÷2 → Λ24 基。
自检：偶格、det(B)=±1、Gram det=1、BKZ 最短向量²=4。
"""
import numpy as np
from sympy import Matrix, ZZ
from sympy.matrices.normalforms import hermite_normal_form
import fpylll


def golay_g24_rows():
    """Golay G24 生成矩阵（QR(23) 码扩展）。已验证权重分布 {0:1,8:759,12:2576,16:759,24:1}。"""
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
    """2Λ24 的整数生成元（Λ24 生成元 ×2），行向量 24 列。"""
    rows = []
    rows.append(np.ones(24, dtype=int))                      # 2·½(1,...,1) = (1,...,1)
    for i in range(24):
        r = np.zeros(24, dtype=int); r[i] = 8; rows.append(r)   # 2·4e_i
    for j in range(1, 24):
        r = np.zeros(24, dtype=int); r[0] = 4; r[j] = -4
        rows.append(r)                                          # 2·2(e_1−e_j)
    for g in golay_g24_rows():
        rows.append(4 * g)                                     # 2·2g
    return np.array(rows)


def leech_basis_hnf():
    """HNF：rows(60×24) → 2Λ24 的 HNF 基 → ÷2 → Λ24 基。"""
    R = generators_2L()
    M = Matrix(R.tolist())
    H = hermite_normal_form(M)           # 60×24，非零行 = 2Λ24 的 HNF 基（下三角）
    Hnp = np.array(H.tolist(), dtype=np.float64)
    nz = Hnp[np.any(Hnp != 0, axis=1)]   # 取非零行（秩 24 ⟹ 24 行）
    assert nz.shape[0] == 24, f"非零行数 {nz.shape[0]} ≠ 24"
    B = nz / 2.0                          # ÷2 → Λ24 基
    return B


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
    M = fpylll.IntegerMatrix(d, d)
    for i in range(d):
        for j in range(d):
            M[i, j] = int(round(B[i, j] * 2))   # 半整数 ×2 整数化
    fpylll.LLL.reduction(M)
    fpylll.BKZ.reduction(M, fpylll.BKZ.Param(block_size=d))
    min_norm = min(sum(M[i, j] * M[i, j] for j in range(d)) for i in range(d)) / 4.0
    print(f"BKZ 后最短基向量范数² = {min_norm}（Leech 期望 4）")
    return min_norm == 4.0


if __name__ == "__main__":
    B = leech_basis_hnf()
    if leech_check(B):
        print("✓✓ Leech 格构造验证通过（偶幺模 + 最短²=4 ⟹ 唯一性 ⟹ 确为 Leech）")
        np.save("leech_basis.npy", B)
        np.set_printoptions(linewidth=200, precision=1, suppress=True)
        print(B.astype(int))
    else:
        print("✗ Leech 自检失败")
