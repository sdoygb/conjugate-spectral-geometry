#!/usr/bin/env python3
"""κ 闭式推导——暴力裁决（修复版）
1. r=1 的 κ_avg 闭式验证（均匀类内平均）
2. r>=2 的 κ_avg 闭式验证（m=5,6,7）
3. κ_enum（枚举解码器）vs κ_avg——解码器依赖量化
"""
import itertools
import numpy as np
from math import comb

def pc(x): return bin(x).count('1') & 1

def rm_basis(r, m):
    gens = []
    for deg in range(r+1):
        for S in itertools.combinations(range(m), deg):
            v = 0
            for x in range(1<<m):
                val = 1
                for i in S:
                    if not (x >> i) & 1: val = 0; break
                v |= (val << x)
            gens.append((S, v))
    return gens

def gauss_binomial(n, k, q=2):
    num = 1; den = 1
    for i in range(1, k+1):
        num *= (q**(n-k+i) - 1)
        den *= (q**i - 1)
    return num // den

def flat_rank(points, m):
    p0 = points[0]
    diffs = [p ^ p0 for p in points[1:]]
    rk = 0; basis = []
    for v in diffs:
        for b in basis:
            v = min(v, v ^ b)
        if v: basis.append(v); rk += 1
    return rk

def aff_hull_mask(points, m):
    p0 = points[0]
    diffs = [p ^ p0 for p in points[1:]]
    basis = []
    for v in diffs:
        for b in basis:
            v = min(v, v ^ b)
        if v: basis.append(v)
    mask = 0
    for combo_mask in range(1 << len(basis)):
        x = p0
        for j, b in enumerate(basis):
            if (combo_mask >> j) & 1: x ^= b
        mask |= (1 << x)
    return mask

def kappa_avg_r1(m):
    """r=1 的 κ_avg 闭式"""
    return 2**(m-2) * (2**m - 2**(m-2)) / ((2**m - 1) * (2**(m-1) - 1))

def kappa_avg_rge2(r, m):
    """r>=2 的 κ_avg 闭式"""
    return 2**((r+1)*(m-r-1)) / gauss_binomial(m, r+1)

# ============ 裁决 2（修复）：r=1 的 κ_avg 闭式 ============
print("=" * 60)
print("裁决 2: r=1 的 κ_avg（均匀类内平均）——闭式 vs 暴力")
for m in (4, 5, 6):
    kc = kappa_avg_r1(m)
    zl1 = None
    for S, v in rm_basis(2, m):
        if len(S) == 2: zl1 = v; break
    rng2 = np.random.default_rng(m * 100)
    flip_sum = 0; cnt = 0
    for _ in range(30000):
        a, b = [int(x) for x in rng2.choice(1 << m, 2, replace=False)]
        flats = 0; flips = 0
        for c in range(1 << m):
            if c in (a, b): continue
            d = a ^ b ^ c
            if d in (a, b, c): continue
            if c >= d: continue  # 避免重复计数
            pts = [a, b, c, d]
            if flat_rank(pts, m) == 2:
                flats += 1
                P = aff_hull_mask(pts, m)
                flips += pc(P & zl1)
        if flats != 2**(m-1) - 1:
            print(f"  m={m}: 包含平坦数 = {flats}（理论 {2**(m-1)-1}）——错误"); break
        flip_sum += flips; cnt += flats
    print(f"m={m}: 闭式 κ_avg = {kc:.6f} | 暴力 = {flip_sum/cnt:.6f} | 一致 = {abs(kc - flip_sum/cnt) < 0.005}")

# ============ 裁决 1b：r>=2 的 κ_avg 闭式（m=5,6,7） ============
print("=" * 60)
print("裁决 1b: r>=2 的 κ_avg（均匀）——闭式 vs 暴力采样")
for (r, m) in [(2, 5), (2, 6), (2, 7), (3, 7)]:
    kc = kappa_avg_rge2(r, m)
    zl = None
    for S, v in rm_basis(r+1, m):
        if len(S) == r+1: zl = v; break
    rng = np.random.default_rng(r * 1000 + m)
    flip = 0; cnt = 0
    N = 100000
    wt = 2**r
    for _ in range(N):
        A = [int(x) for x in rng.choice(1 << m, wt, replace=False)]
        if flat_rank(A, m) != r + 1:  # 主阶层
            continue
        cnt += 1
        P = aff_hull_mask(A, m)
        if bin(P).count('1') != 2**(r+1):
            print("错误：仿射包大小不符"); break
        flip += pc(P & zl)
    print(f"r={r}, m={m}: 闭式 κ_avg = {kc:.6f} | 暴力 = {flip/cnt:.6f} | 一致 = {abs(kc - flip/cnt) < 0.005}")

# ============ 裁决 3：κ_enum（枚举解码器）vs κ_avg ============
print("=" * 60)
print("裁决 3: κ_enum（itertools 枚举解码器）vs κ_avg（均匀）")
def kappa_enum(m, r, nsamp=80000):
    n = 1 << m
    zl = None
    for S, v in rm_basis(r+1, m):
        if len(S) == r+1: zl = v; break
    z_supps = [v for _, v in rm_basis(r, m)]
    table = {}
    for w in range(3):
        for E in itertools.combinations(range(n), w):
            mask = sum(1 << i for i in E)
            s = 0
            for j, g in enumerate(z_supps): s |= pc(mask & g) << j
            if s not in table: table[s] = mask
    rng = np.random.default_rng(7)
    amb = 0; flip = 0
    for _ in range(nsamp):
        pos = [int(x) for x in rng.choice(n, 2, replace=False)]
        mask = sum(1 << i for i in pos)
        s = 0
        for j, g in enumerate(z_supps): s |= pc(mask & g) << j
        Es = table.get(s, 0)
        if Es != mask:
            amb += 1
            if pc((mask ^ Es) & zl): flip += 1
    return flip / amb if amb else float('nan')

for m in (4, 5, 6):
    ke = kappa_enum(m, 1)
    kc = kappa_avg_r1(m)
    print(f"r=1, m={m}: κ_enum = {ke:.4f} | κ_avg = {kc:.4f} | 比值 = {ke/kc:.4f}")

# ============ 裁决 4：r=2, m=6 的 κ_enum（模拟 V2） ============
print("=" * 60)
print("裁决 4: r=2, m=6 的 κ_enum（枚举解码器，w=4 层）——是否 = V2 实测 0.189？")
m, r = 6, 2
n = 1 << m
zl = None
for S, v in rm_basis(r+1, m):
    if len(S) == r+1: zl = v; break
z_supps = [v for _, v in rm_basis(r, m)]
table = {}
for w in range(5):
    for E in itertools.combinations(range(n), w):
        mask = sum(1 << i for i in E)
        s = 0
        for j, g in enumerate(z_supps): s |= pc(mask & g) << j
        if s not in table: table[s] = mask
print(f"解码表大小 = {len(table)} / syndrome 空间 {2**len(z_supps)}")
rng = np.random.default_rng(9)
amb = 0; flip = 0
N = 200000
for _ in range(N):
    pos = [int(x) for x in rng.choice(n, 4, replace=False)]
    mask = sum(1 << i for i in pos)
    s = 0
    for j, g in enumerate(z_supps): s |= pc(mask & g) << j
    Es = table.get(s, 0)
    if Es != mask:
        amb += 1
        if pc((mask ^ Es) & zl): flip += 1
print(f"κ_enum = {flip/amb:.6f} | κ_avg = {kappa_avg_rge2(2,6):.6f} | V2 实测 ≈ 0.186-0.189")
