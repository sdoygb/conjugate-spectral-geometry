# -*- coding: utf-8 -*-
"""d8_w6.py —— [[64,20,8]] (CSS(RM(2,6))) 权重 6 层全枚举（C(64,6) = 74,974,368 个 flip 集）

流式：numpy 分批生成组合 → XOR 求 syndrome → searchsorted 跨层检测（权重 6 syndrome
首分量为 0，只可能与权重 2/4 层同类）→ np.unique 批内统计 → 全局 Counter 合并。

输出：fail(6)、跨层数、非跨层类数、类大小分布、p^6 / θ^12 系数。
"""
import itertools, time
from collections import Counter
import numpy as np

m, r = 6, 2
n = 1 << m
BATCH = 2_000_000

# ---- RM(2,6) 校验列（22 位 syndrome 列） ----
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
cols_arr = np.array(cols, dtype=np.int64)
assert len(set(cols)) == n and len(monos) == 22

# ---- 跨层候选：权重 2 ∪ 权重 4 的 syndrome 集合 ----
known = set()
for w in (2, 4):
    for comb in itertools.combinations(range(n), w):
        s = 0
        for i in comb:
            s ^= cols[i]
        known.add(s)
known_arr = np.array(sorted(known), dtype=np.int64)
print(f'跨层候选 syndrome（权重2∪4）: {len(known_arr):,}', flush=True)

def gen_batch():
    it = itertools.combinations(range(n), 6)
    while True:
        chunk = list(itertools.islice(it, BATCH))
        if not chunk:
            break
        yield np.array(chunk, dtype=np.int64)

t0 = time.time()
cross = 0
total = 0
cnt_global = Counter()
for b, arr in enumerate(gen_batch()):
    syms = np.bitwise_xor.reduce(cols_arr[arr], axis=1)
    idx = np.searchsorted(known_arr, syms)
    idx = np.clip(idx, 0, len(known_arr) - 1)
    is_known = known_arr[idx] == syms
    cross += int(is_known.sum())
    sub = syms[~is_known]
    vals, counts = np.unique(sub, return_counts=True)
    cnt_global.update(dict(zip(vals.tolist(), counts.tolist())))
    total += len(arr)
    if (b + 1) % 10 == 0:
        print(f'  {total/1e6:.0f}M / 75M, 跨层 {cross:,}, 非跨层类 {len(cnt_global):,}, {time.time()-t0:.0f}s', flush=True)

noncross_total = total - cross
n_classes = len(cnt_global)
fail = cross + (noncross_total - n_classes)
print()
print(f'权重6 flip 总数      = {total:,}')
print(f'跨层（syndrome∈权重2∪4） = {cross:,}   ({cross/total:.6f})')
print(f'非跨层总数           = {noncross_total:,}')
print(f'非跨层类数           = {n_classes:,}')
print(f'fail(6)             = {fail:,}   ({fail/total:.6f})')
hist = Counter(cnt_global.values())
print('非跨层类大小分布（前 12 大）:')
for v in sorted(hist, reverse=True)[:12]:
    print(f'  v={v}: {hist[v]:,} 类')
print(f'p^6 系数 = {fail:,}')
print(f'θ^12 系数 = {fail}/4096 = {fail/4096:.2f}')
print(f'耗时 {time.time()-t0:.0f}s')
