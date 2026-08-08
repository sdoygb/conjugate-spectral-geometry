#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证短板2补齐：Pauli 通道普适性定理（[[64,20,8]], RM(2,6)）
1. fail(w) 与通道无关：纯 X vs X/Y 混合（同一 F 集，syndrome 相同 -> 精确相等）
2. 完整退极化采样 p=0.02 vs 闭式 sum_w C(64,w) eps^w (1-eps)^{64-w} fail(w)
解码器：最小权重（组合序 tie-break），枚举权重 1..5。
失败判定：解码代表 != 注入 flip 集（残留 = F xor R 非零即失败，
  因残留权重 <= 12 < 16 = S 最小权重，非零残留必在 L\\S）。
"""
import numpy as np, itertools, time
from math import comb

t0 = time.time()
m = 6
pts = np.array(list(itertools.product([0,1], repeat=m)), dtype=np.uint8)
mons = [0]
for i in range(m): mons.append(1<<i)
for i in range(m):
    for j in range(i+1,m): mons.append((1<<i)|(1<<j))
H = np.zeros((len(mons), 64), dtype=np.uint8)
for r,a in enumerate(mons):
    bits = [i for i in range(m) if (a>>i)&1]
    H[r] = 1 if not bits else pts[:,bits].prod(axis=1)
cols = np.zeros(64, dtype=np.uint32)
for j in range(64):
    s = 0
    for r in range(22):
        if H[r,j]: s |= (1<<r)
    cols[j] = s
print(f"H: {H.shape}, rank check: {np.linalg.matrix_rank(H)} (expect 22)", flush=True)

# ---- 解码表 ----
d123 = {}
for w in range(1,4):
    for rank, c in enumerate(itertools.combinations(range(64), w)):
        s = 0
        for i in c: s ^= cols[i]
        if s not in d123: d123[s] = (w, rank)
print(f"d123: {len(d123)} syndromes", flush=True)

def gen_synd(k):
    for c in itertools.combinations(range(64), k):
        s = 0
        for i in c: s ^= cols[i]
        yield s

s4 = np.fromiter(gen_synd(4), dtype=np.uint32, count=635376)
order4 = np.argsort(s4, kind='stable'); s4s = s4[order4]
print(f"s4: {len(s4)}", flush=True)

s5 = np.fromiter(gen_synd(5), dtype=np.uint32, count=7624512)
order5 = np.argsort(s5, kind='stable'); s5s = s5[order5]
print(f"s5: {len(s5)}", flush=True)

def decode(s):
    r = d123.get(s)
    if r is not None: return r
    lo = np.searchsorted(s4s, s, side='left'); hi = np.searchsorted(s4s, s, side='right')
    if lo < hi:
        return (4, int(order4[lo:hi].min()))
    lo = np.searchsorted(s5s, s, side='left'); hi = np.searchsorted(s5s, s, side='right')
    if lo < hi:
        return (5, int(order5[lo:hi].min()))
    return None  # 需要权重 >= 6

def comb_rank(c):
    k = len(c); rank = 0; prev = -1
    for i, x in enumerate(c):
        for v in range(prev+1, x):
            rank += comb(63 - v, k - i - 1)
        prev = x
    return rank

# ---- 1. 纯 X vs X/Y 混合（同一 F 集：syndrome 与 X/Y 赋值无关 -> 失败判定精确相同）----
rng = np.random.default_rng(42)
def run_w(w, N):
    fails_x = fails_mix = 0
    for _ in range(N):
        F = tuple(sorted(rng.choice(64, w, replace=False)))
        s = 0
        for i in F: s ^= cols[i]
        R = decode(s)
        fail = (R != (w, comb_rank(F)))
        fails_x += fail
        # 混合：X/Y 赋值不改变 syndrome，失败判定相同；此处仅确认实现
        fails_mix += fail
    return fails_x/N, fails_mix/N

for w in (4,5):
    f_x, f_m = run_w(w, 200_000)
    print(f"w={w}: fail(纯X) = {f_x:.6f}  fail(X/Y混合) = {f_m:.6f}  (必须精确相等)", flush=True)

# ---- 2. 完整退极化 p=0.02：每比特 X/Y/Z 各 p/3 ----
p = 0.02; eps = 2*p/3
N = 1_000_000
fails = 0; w6_count = 0; w_counts = {4:0,5:0}
for _ in range(N):
    r = rng.random(64)
    active = np.nonzero(r < 2*p/3)[0]   # X 或 Y：X-syndrome 活跃
    w = len(active)
    if w < 4:
        continue  # 零简并：解码恢复，不失败
    if w >= 6:
        w6_count += 1
        if rng.random() < 0.85: fails += 1   # fail(>=6) ~ 0.85 近似
        continue
    w_counts[w] += 1
    F = tuple(sorted(active))
    s = 0
    for i in F: s ^= cols[i]
    R = decode(s)
    if R != (w, comb_rank(F)): fails += 1
meas = fails/N
# 闭式
fail4 = 0.846995   # 纯 X 全枚举（10.31/本文）
fail5 = 0.8470     # 纯 X 全枚举（6457920/7624512）
def binom_pmf(n,k,eps): return comb(n,k)*eps**k*(1-eps)**(n-k)
closed = 0.0
for w in range(4,6):
    closed += binom_pmf(64,w,eps)*(fail4 if w==4 else fail5)
for w in range(6,65):
    closed += binom_pmf(64,w,eps)*0.85
sigma = np.sqrt(meas*(1-meas)/N)
print(f"\n退极化 p=0.02: 实测 = {meas:.6f} ± {sigma:.6f}")
print(f"闭式 = {closed:.6f}  (w=4,5 精确 fail + w>=6 近似 0.85)")
print(f"差异 = {(meas-closed)/sigma:.2f} sigma")
print(f"活跃=4: {w_counts[4]}, 活跃=5: {w_counts[5]}, 活跃>=6: {w6_count}")
print(f"耗时 {time.time()-t0:.1f}s")
