# -*- coding: utf-8 -*-
"""d8_enumerate.py —— d=8 档 ([[64,20,8]], CSS(RM(2,6))) 纯组合全枚举验证

与 mix_enumerate.py（态矢量法，n=16）不同：n=64 的 |0_L⟩ 有 2^42 个分量，
态矢量不可行。这里用纯组合枚举：校验列 syndrome + 按 syndrome 分组 +
min-weight 恢复代表判定（组内首成员 = 代表，其余失败）。

闭式预计算（结构分析，2026-08-07）：
  w=1: 64 个单 flip，列互异 → 64 类×1 成员，fail=0
  w=2: 2016 个对，列对异或 (0, a, Q(v_i)⊕Q(v_j)) 二次部分唯一锁定 i
       → 2016 类×1 成员，fail=0（与 d=4 的 15 类×8 成员完全不同）
  w=3: 41664 个三元组，无跨层（残留 <8 不在码空间）→ 全可解码，fail=0
  w=4: 主阶。类 = {F} ∪ {S8\F : S8 ⊇ F, S8 ∈ 权重8码字(仿射3-子空间)}
       仿射 2-平面（10416 个，Σv=0）：16 成员/类（651 类，平行平面族）
       一般位置（624960 个）：2 成员/类（312480 类，互补对）
       类数 = 313131，fail(4) = Σ(v-1) = 322245，fail(4)=0.5072
       p^4 系数 = 322245；θ^8 系数（解码失败率）= 322245/256 = 1258.77
  w=5: 次主阶（--max-w 5 启用，跨层检测 + 类结构）

用法: python3 d8_enumerate.py [--max-w 4|5]
"""
import argparse
import itertools
import time
from collections import Counter

import numpy as np


def build_cols(r, m):
    """CSS(RM(r,m)) 校验矩阵列：RM(r,m) 单项式在全部 2^m 点上的取值。
    列 = 22 位 int（r=2, m=6）。点 = 整数 0..2^m-1（二进制 = F2^m 向量）。"""
    monos = []
    for size in range(r + 1):
        for comb in itertools.combinations(range(m), size):
            monos.append(comb)
    cols = []
    for x in range(2 ** m):
        col = 0
        for idx, mono in enumerate(monos):
            ok = 1
            for i in mono:
                if not (x >> i) & 1:
                    ok = 0
                    break
            if ok:
                col |= 1 << idx
        cols.append(col)
    return np.array(cols, dtype=np.int64), len(monos)


def layer_syndromes(cols, n, w):
    """权重 w 全部 flip 集的 syndrome（向量化 XOR reduce）。"""
    combos = np.array(list(itertools.combinations(range(n), w)), dtype=np.int64)
    syms = np.bitwise_xor.reduce(cols[combos], axis=1)
    return syms


def layer_syndromes_batched(cols, n, w, batch=1_000_000):
    """分批生成权重 w 的 syndrome，避免大组合矩阵峰值内存（权重 5 用）。"""
    it = itertools.combinations(range(n), w)
    while True:
        chunk = list(itertools.islice(it, batch))
        if not chunk:
            break
        arr = np.array(chunk, dtype=np.int64)
        yield np.bitwise_xor.reduce(cols[arr], axis=1)


def run_layers(cols, n, max_w):
    """枚举权重 1..max_w：按 syndrome 分组，组内首成员（min 权重 + 组合序）为恢复代表。
    返回每层的 (类数, 失败数, 类大小直方图)。"""
    recs = []  # (syndrome, weight, order)
    for w in range(1, max_w + 1):
        t0 = time.time()
        syms = layer_syndromes(cols, n, w)
        recs.extend(zip(syms.tolist(), [w] * len(syms), range(len(syms))))
        print(f'  权重 {w}: C({n},{w}) = {len(syms)}  flip 集生成完毕 '
              f'({time.time()-t0:.1f}s)')
    t0 = time.time()
    recs.sort(key=lambda t: t[0])  # 稳定排序 → 组内保持 (weight, order) 序
    stats = {w: {'classes': 0, 'fails': 0, 'sizes': Counter()}
             for w in range(1, max_w + 1)}
    i, N = 0, len(recs)
    while i < N:
        s = recs[i][0]
        j = i
        while j < N and recs[j][0] == s:
            j += 1
        v = j - i
        rep_w = recs[i][1]
        stats[rep_w]['classes'] += 1
        stats[rep_w]['sizes'][v] += 1
        for k in range(i, j):
            w = recs[k][1]
            if k > i:  # 非代表 → 失败
                stats[w]['fails'] += 1
        i = j
    print(f'  分组统计完毕 ({time.time()-t0:.1f}s)')
    return stats


def count_affine_planes(n, w=4):
    """权重 4 flip 集中仿射 2-平面的数量（Σv = 0 ⟺ 仿射 2-平面）。"""
    cnt = 0
    plane_sets = set()
    for comb in itertools.combinations(range(n), w):
        s = 0
        for i in comb:
            s ^= i
        if s == 0:
            cnt += 1
            plane_sets.add(comb)
    return cnt, plane_sets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-w', type=int, default=4, choices=[4, 5])
    args = ap.parse_args()
    r, m = 2, 6
    n = 1 << m
    cols, nrows = build_cols(r, m)
    k = n - 2 * nrows
    print(f'码: CSS(RM({r},{m})) [[{n},{k},8]]   校验行数 {nrows}')
    assert nrows == 22 and k == 20
    assert len(set(cols.tolist())) == n, '校验列必须互异'

    # ---- 阶段 1+2：权重 ≤4 ----
    t0 = time.time()
    stats = run_layers(cols, n, args.max_w)
    print(f'\n=== 权重 1..{args.max_w} 全枚举（{time.time()-t0:.1f}s）===')
    print(f'{"w":>3} {"C(n,w)":>9} {"类数":>9} {"失败数":>9} {"fail(w)":>10}  类大小分布')
    total_fail = 0
    for w in range(1, args.max_w + 1):
        st = stats[w]
        cw = len(list(itertools.combinations(range(n), w)))
        fail_ratio = st['fails'] / cw if cw else 0.0
        total_fail += st['fails']
        hist = ', '.join(f'{v}×{c}' for v, c in sorted(st['sizes'].items()))
        print(f'{w:>3} {cw:>9} {st["classes"]:>9} {st["fails"]:>9} '
              f'{fail_ratio:>10.5f}  {hist}')

    # ---- 闭式对照 ----
    print('\n=== 闭式对照（预计算）===')
    print(f'权重4 类数  枚举 {stats[4]["classes"]}  vs 闭式 313131')
    print(f'权重4 失败  枚举 {stats[4]["fails"]}  vs 闭式 322245')
    print(f'fail(4)     枚举 {stats[4]["fails"]/635376:.6f}  vs 闭式 0.5072')
    main_fail = stats[4]['fails']   # 主阶 = 权重 4 层（w0 = d/2 = 4）
    print(f'p^4 系数    = {main_fail}  (主阶，随机 Pauli)')
    print(f'θ^8 系数    = {main_fail}/256 = {main_fail/256:.4f}  (解码失败率版本)')
    kappa = 2 ** ((r + 1) * (m - r - 1)) / (
        np.prod([2 ** m - 2 ** i for i in range(r + 1)]) /
        np.prod([2 ** (r + 1) - 2 ** i for i in range(r + 1)]))
    print(f'κ₂(6)       = {kappa:.6f}  (闭式 512/1395 = 0.3670)')
    print(f'loss_Z θ^8  = {main_fail/256*kappa:.3f}  (逻辑 Z 翻转率版本)')
    if args.max_w >= 5:
        f5 = stats[5]['fails']
        print(f'p^5 系数    = {f5}  (次主阶，权重 5 层)')
        print(f'θ^10 系数   = {f5}/1024 = {f5/1024:.4f}  (解码失败率版本)')

    # ---- 平面交叉验证（几何分析）----
    n_plane, plane_sets = count_affine_planes(n)
    print(f'\n=== 仿射 2-平面交叉验证 ===')
    print(f'Σv=0 的 4 点集（仿射 2-平面）: {n_plane}  vs 闭式 10416 = 651×16')
    combos4 = list(itertools.combinations(range(n), 4))
    syms4 = np.bitwise_xor.reduce(cols[np.array(combos4, dtype=np.int64)], axis=1)
    size_of = Counter(syms4.tolist())
    plane_bad = sum(1 for c in plane_sets
                    if size_of[np.bitwise_xor.reduce(cols[list(c)])] != 16)
    plane_good = n_plane - plane_bad
    print(f'平面 4 点集所在类大小: 16 的类 {plane_good} 个，非 16 的类 {plane_bad} 个')
    nonplane_bad = sum(1 for c in combos4
                       if c not in plane_sets
                       and size_of[np.bitwise_xor.reduce(cols[list(c)])] == 16)
    print(f'非平面 4 点集落入 16 成员类: {nonplane_bad} 个 (应为 0)')

    # ---- 阶段 3：权重 5 次主阶 ----
    if args.max_w >= 5:
        t0 = time.time()
        c5 = 7624512
        chunks = list(layer_syndromes_batched(cols, n, 5))
        syms5 = np.concatenate(chunks)
        print(f'  权重 5: {len(syms5)}  flip 集生成完毕 ({time.time()-t0:.1f}s)')
        # 权重 ≤4 的 syndrome 全集（跨层检测）
        known4 = set()
        for w in range(1, 5):
            known4 |= set(layer_syndromes(cols, n, w).tolist())
        t1 = time.time()
        cross = 0
        for s in syms5.tolist():
            if s in known4:
                cross += 1
        print(f'\n=== 权重 5 次主阶（跨层扫描 {time.time()-t1:.1f}s）===')
        print(f'C(64,5) = {c5}')
        print(f'跨层（syndrome 落在权重≤4 空间）: {cross} 个 flip')
        # 非跨层部分：内部类统计（numpy unique）
        known_arr = np.fromiter(known4, dtype=np.int64, count=len(known4))
        mask = np.isin(syms5, known_arr)
        syms5_nc = syms5[~mask]
        uniq, counts = np.unique(syms5_nc, return_counts=True)
        cls5 = len(uniq)
        fail5 = int((counts - 1).sum()) + cross  # 跨层 flip 全失败
        size_hist = ', '.join(f'{v}×{c}' for v, c in
                              sorted(Counter(counts.tolist()).items()))
        print(f'类数(非跨层) {cls5}，类大小分布: {size_hist}')
        print(f'fail(5) = {fail5}  ({fail5/c5:.6f})')
        print(f'p^5 系数 = {fail5}；θ^10 系数 = {fail5}/1024 = {fail5/1024:.4f}')


if __name__ == '__main__':
    main()
