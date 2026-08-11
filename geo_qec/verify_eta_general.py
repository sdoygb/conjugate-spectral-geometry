#!/usr/bin/env python3
"""
η = 1/3 一般证明的数值验证（m = 7, 8）
========================================
完备方向码 [[2^m-1, 2^m-1-2m, 3]] = CSS(H_m, H_m)（10.28 定理 10.28.1.02），
H_m 列 = 全部非零 m-bit 向量（1..2^m-1）。

验证目标（10.44 定理 10.44.2.01 的一般证明，一切 m ≥ 3）：
  误恢复数 = 3·C(n,2)（每共线位置对恰 3 型：X_aX_b, Z_aZ_b, Y_aY_b），
  η = 3·C(n,2) / (9·C(n,2)) = 1/3。

判定逻辑（与 10.44 定义 10.44.2.01 一致）：
  1. 权重 2 Pauli 错误 E，syndrome(E) = (H_m·X 部分, H_m·Z 部分)（F₂ 列 XOR）；
  2. 若 syndrome(E) 与某单比特 Q 相同（查表），恢复算符 R = Q；
  3. 残留 E_res = Q·E；E_res 为逻辑算符 ⟺ syndrome(E_res) = 0
     且 (X 部分, Z 部分) 不全在行空间（行空间 = 单纯码，非零元素权重 2^{m-1}）。

运行: python3 geo_qec/verify_eta_general.py
"""
from itertools import combinations


def build_code(m):
    n = 2 ** m - 1
    cols = [i + 1 for i in range(n)]            # 列 = 非零 m-bit 向量
    rows = []                                    # H_m 的行（标准基泛函）
    for r in range(m):
        rows.append(frozenset(j for j in range(n) if (cols[j] >> r) & 1))
    # 行空间（X/Z 稳定子支撑）= 单纯码 [2^m-1, m, 2^{m-1}]
    rowspace = set()
    for mask in range(2 ** m):
        supp = set()
        for r in range(m):
            if (mask >> r) & 1:
                supp.symmetric_difference_update(rows[r])
        rowspace.add(frozenset(supp))

    def col_synd(S):
        s = 0
        for j in S:
            s ^= cols[j]
        return s

    single = {}                                  # 单比特 syndrome 表
    for i in range(n):
        ci = cols[i]
        single[(ci, 0)] = (i, 1)                 # X_i → (h_i, 0)
        single[(0, ci)] = (i, 2)                 # Z_i → (0, h_i)
        single[(ci, ci)] = (i, 3)                # Y_i → (h_i, h_i)

    def is_logical(Sx, Sz):
        # 与全部稳定子对易 ⟺ syndrome 为零
        if col_synd(Sx) != 0 or col_synd(Sz) != 0:
            return False
        # 不在稳定子群 ⟺ X 部分或 Z 部分不在行空间
        return not (frozenset(Sx) in rowspace and frozenset(Sz) in rowspace)

    return n, cols, single, is_logical, col_synd


def add_pauli(Sx, Sz, pos, t):
    """把类型 t 的 Pauli（1=X, 2=Z, 3=Y）作用在 pos 位加入 (Sx, Sz)"""
    if t == 1:
        Sx.add(pos)
    elif t == 2:
        Sz.add(pos)
    else:
        Sx.add(pos)
        Sz.add(pos)


def main():
    for m in (7, 8):
        n, cols, single, is_logical, col_synd = build_code(m)
        total = 9 * n * (n - 1) // 2
        mis = 0
        per_type = {'XX': 0, 'ZZ': 0, 'YY': 0, 'mixed': 0}
        for a, b in combinations(range(n), 2):
            for ta in (1, 2, 3):
                for tb in (1, 2, 3):
                    Sx, Sz = set(), set()
                    add_pauli(Sx, Sz, a, ta)
                    add_pauli(Sx, Sz, b, tb)
                    s = (col_synd(Sx), col_synd(Sz))
                    if s in single:
                        qi, qt = single[s]
                        # 残留 = Q · E（Pauli 乘法，X/Z 部分分别 XOR）
                        RSx, RSz = set(Sx), set(Sz)
                        if qt == 1:
                            RSx.symmetric_difference_update([qi])
                        elif qt == 2:
                            RSz.symmetric_difference_update([qi])
                        else:
                            RSx.symmetric_difference_update([qi])
                            RSz.symmetric_difference_update([qi])
                        if is_logical(RSx, RSz):
                            mis += 1
                            key = ('XX' if ta == tb == 1 else
                                   'ZZ' if ta == tb == 2 else
                                   'YY' if ta == tb == 3 else 'mixed')
                            per_type[key] += 1
        eta = mis / total
        expect = 3 * n * (n - 1) // 2
        print(f"m={m}: n={n}, total={total}, misrecovered={mis}, "
              f"eta={eta:.10f}")
        print(f"    期望 3·C(n,2) = {expect}   per_type = {per_type}")
        assert mis == expect, "误恢复数 != 3·C(n,2)"
        assert eta == 1 / 3, "η != 1/3"
        print("    ✓ η = 1/3 精确成立；纯型 3·C(n,2)、混合型 0")
    print("ALL PASS")


if __name__ == '__main__':
    main()
