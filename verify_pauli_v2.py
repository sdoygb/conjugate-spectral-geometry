#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短板2验证 v2：fail(4)/fail(5) 全枚举精确值 + 退极化 p=0.02 vs 闭式
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

d123 = {}
for w in range(1,4):
    for rank, c in enumerate(itertools.combinations(range(64), w)):
        s = 0
        for i in c: s ^= cols[i]
        if s not in d123: d123[s] = (w, rank)
d4 = {}
for rank, c in enumerate(itertools.combinations(range(64), 4)):
    s = cols[c[0]]^cols[c[1]]^cols[c[2]]^cols[c[3]]
    if s not in d4: d4[s] = (4, rank)
print(f"d123: {len(d123)}, d4: {len(d4)}", flush=True)

def gen_synd(k):
    for c in itertools.combinations(range(64), k):
        s = 0
        for i in c: s ^= cols[i]
        yield s
s5 = np.fromiter(gen_synd(5), dtype=np.uint32, count=7624512)
order5 = np.argsort(s5, kind='stable'); s5s = s5[order5]
print(f"s5 built ({time.time()-t0:.0f}s)", flush=True)

def comb_rank(c):
    k = len(c); rank = 0; prev = -1
    for i, x in enumerate(c):
        for v in range(prev+1, x):
            rank += comb(63 - v, k - i - 1)
        prev = x
    return rank

def decode(s):
    r = d123.get(s)
    if r is not None: return r
    r = d4.get(s)
    if r is not None: return r
    lo = np.searchsorted(s5s, s, side='left'); hi = np.searchsorted(s5s, s, side='right')
    if lo < hi:
        return (5, int(order5[lo:hi].min()))
    return None

# ---- 全枚举 fail(4) ----
fails4 = 0
for rank, c in enumerate(itertools.combinations(range(64), 4)):
    s = cols[c[0]]^cols[c[1]]^cols[c[2]]^cols[c[3]]
    if decode(s) != (4, rank): fails4 += 1
fail4 = fails4/635376
print(f"fail(4) 全枚举 = {fail4:.9f}  ({fails4}/635376)  [{time.time()-t0:.0f}s]", flush=True)

# ---- 全枚举 fail(5) ----
fails5 = 0
for rank, c in enumerate(itertools.combinations(range(64), 5)):
    s = 0
    for i in c: s ^= cols[i]
    if decode(s) != (5, rank): fails5 += 1
fail5 = fails5/7624512
print(f"fail(5) 全枚举 = {fail5:.9f}  ({fails5}/7624512)  [{time.time()-t0:.0f}s]", flush=True)

# ---- 退极化 p=0.02 采样 ----
rng = np.random.default_rng(42)
p = 0.02; eps = 2*p/3
N = 1_000_000
fails = 0; w6_count = 0
for _ in range(N):
    r = rng.random(64)
    active = np.nonzero(r < 2*p/3)[0]
    w = len(active)
    if w < 4: continue
    if w >= 6:
        w6_count += 1
        if rng.random() < 0.85: fails += 1
        continue
    F = tuple(sorted(active))
    s = 0
    for i in F: s ^= cols[i]
    if decode(s) != (w, comb_rank(F)): fails += 1
meas = fails/N
def binom_pmf(n,k,e): return comb(n,k)*e**k*(1-e)**(n-k)
closed = binom_pmf(64,4,eps)*fail4 + binom_pmf(64,5,eps)*fail5
for w in range(6,65): closed += binom_pmf(64,w,eps)*0.85
sigma = np.sqrt(meas*(1-meas)/N)
print(f"\n退极化 p=0.02: 实测 = {meas:.6f} ± {sigma:.6f}  闭式 = {closed:.6f}  差异 = {(meas-closed)/sigma:.2f}σ")
print(f"  w=4 项 = {binom_pmf(64,4,eps)*fail4:.6f}, w=5 项 = {binom_pmf(64,5,eps)*fail5:.6f}, w>=6 项 = {closed-binom_pmf(64,4,eps)*fail4-binom_pmf(64,5,eps)*fail5:.6f}")
print(f"  w6 样本 = {w6_count}, 耗时 {time.time()-t0:.0f}s")
