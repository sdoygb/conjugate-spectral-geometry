#!/usr/bin/env python3
"""κ 闭式推导的暴力裁决脚本
κ = 类内逻辑翻转比例 = P(χ_P·zl = 1)
关键问题：
  A) κ_avg（均匀解码器假设）：r=1 闭式 = 2^{m-2}(2^m-2^{m-2})/[(2^m-1)(2^{m-1}-1)]
                            r>=2 闭式 = 2^{(r+1)(m-r-1)}/[m choose r+1]_2
  B) κ_enum（枚举解码器）：模拟 itertools 枚举顺序——与 V2 实测对比
裁决 r=2,m=6 的矛盾：解析 0.367 vs V2 实测 0.189
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
    """点集的仿射包维数（F2）"""
    p0 = points[0]
    diffs = [p ^ p0 for p in points[1:]]
    rk = 0; basis = []
    for v in diffs:
        for b in basis:
            v = min(v, v ^ b)
        if v: basis.append(v); rk += 1
    return rk

def aff_hull_mask(points, m):
    """仿射包指示向量（作为整数掩码）"""
    p0 = points[0]
    diffs = [p ^ p0 for p in points[1:]]
    basis = []
    for v in diffs:
        for b in basis:
            v = min(v, v ^ b)
        if v: basis.append(v)
    # 仿射包 = p0 + span(basis)
    mask = 0
    for combo_mask in range(1 << len(basis)):
        x = p0
        for j, b in enumerate(basis):
            if (combo_mask >> j) & 1: x ^= b
        mask |= (1 << x)
    return mask

# ============ 裁决 1：r=2, m=6 的 κ（均匀平均） ============
print("=" * 60)
print("裁决 1: r=2, m=6 —— κ(均匀) = P(随机3维U 与固定3维W 互补)")
m, r = 6, 2
W_dim = m - r - 1
zl = None
for S, v in rm_basis(r+1, m):
    if len(S) == r+1: zl = v; break
print(f"zl 支撑大小 = {bin(zl).count('1')}（应为 2^{m-r-1} = {2**(m-r-1)}）")
# 采样随机 A（权重 2^r = 4，仿射包 3）
rng = np.random.default_rng(42)
N = 200000
flip_avg = 0
flip_avg_count = 0
for _ in range(N):
    A = rng.choice(1 << m, 4, replace=False)
    A = [int(x) for x in A]
    if flat_rank(A, m) != 3:  # 非主阶层（仿射包必须 = 3）
        continue
    flip_avg_count += 1
    P = aff_hull_mask(A, m)
    if bin(P).count('1') != 8:
        print("错误：仿射包大小 != 8"); break
    flip_avg += pc(P & zl)
k_brute = flip_avg / flip_avg_count
k_formula = 2**((r+1)*(m-r-1)) / gauss_binomial(m, r+1)
print(f"暴力(均匀采样, n={flip_avg_count}): κ = {k_brute:.6f}")
print(f"解析闭式 2^{{(r+1)(m-r-1)}}/[m choose r+1]_2 = {k_formula:.6f}")
print(f"V2 实测（枚举解码器）: κ ≈ 0.186-0.189")

# ============ 裁决 2：r=1 的 κ_avg 闭式（均匀） ============
print("=" * 60)
print("裁决 2: r=1 的 κ_avg（均匀类内平均）闭式")
for m in (4, 5, 6):
    # 闭式
    kc = 2**(m-2) * (2**m - 2**(m-2)) / ((2**m - 1) * (2**(m-1) - 1))
    # 采样验证：随机边 A={a,b}，枚举所有包含 A 的 2-平坦（c⊕d = a⊕b）
    zl1 = None
    for S, v in rm_basis(2, m):
        if len(S) == 2: zl1 = v; break
    rng2 = np.random.default_rng(m * 100)
    flip_sum = 0; cnt = 0
    for _ in range(50000):
        a, b = [int(x) for x in rng2.choice(1 << m, 2, replace=False)]
        # 包含 {a,b} 的 2-平坦：c 任意（≠a,b），d = a^b^c，4 点仿射包 2
        flats = 0; flips = 0
        for c in range(1 << m):
            if c in (a, b): continue
            d = a ^ b ^ c
            if d in (a, b, c): continue
            pts = [a, b, c, d]
            if flat_rank(pts, m) == 2:
                flats += 1
                P = aff_hull_mask(pts, m)
                flips += pc(P & zl1)
        if flats != 2**(m-1) - 1:
            print(f"  m={m}: 包含平坦数 = {flats}（理论 {2**(m-1)-1}）——错误"); break
        flip_sum += flips; cnt += flats
    print(f"m={m}: 闭式 κ_avg = {kc:.6f} | 暴力 = {flip_sum/cnt:.6f}")

# ============ 裁决 3：枚举解码器的 κ_enum（模拟 V2） ============
print("=" * 60)
print("裁决 3: κ_enum（itertools 枚举解码器）——模拟 V2")
def kappa_enum(m, r, nsamp=100000):
    n = 1 << m
    zl = None
    for S, v in rm_basis(r+1, m):
        if len(S) == r+1: zl = v; break
    z_supps = [v for _, v in rm_basis(r, m)]
    # 解码表：枚举顺序（w=0,1,2 升序，itertools 顺序）
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
        w = 2  # 只统计主阶层 w = 2
        pos = [int(x) for x in rng.choice(n, w, replace=False)]
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
    kc = 2**(m-2) * (2**m - 2**(m-2)) / ((2**m - 1) * (2**(m-1) - 1))
    print(f"r=1, m={m}: κ_enum(枚举) = {ke:.4f} | κ_avg(均匀) = {kc:.4f} | V2实测(枚举) ≈ 0.40/0.39/0.38")

# ============ 裁决 4：r=2, m=6 枚举解码器 κ_enum ============
print("=" * 60)
print("裁决 4: r=2, m=6 的 κ_enum（枚举解码器，w=4 层）")
m, r = 6, 2
n = 1 << m
zl = None
for S, v in rm_basis(r+1, m):
    if len(S) == r+1: zl = v; break
z_supps = [v for _, v in rm_basis(r, m)]
print(f"z_supps 数量 = {len(z_supps)}（理论 dim RM(2,6) = {sum(comb(6,k) for k in range(3))}）")
# 解码表：w=0..4
table = {}
for w in range(5):
    for E in itertools.combinations(range(n), w):
        mask = sum(1 << i for i in E)
        s = 0
        for j, g in enumerate(z_supps): s |= pc(mask & g) << j
        if s not in table: table[s] = mask
print(f"解码表大小 = {len(table)}（syndrome 空间 2^{len(z_supps)} = {2**len(z_supps)}）")
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
print(f"κ_enum(枚举) = {flip/amb:.6f}（二义 {amb}, 翻转 {flip}）")
print(f"κ_avg(均匀) = {2**((r+1)*(m-r-1))/gauss_binomial(m, r+1):.6f}")
print(f"V2 实测 κ ≈ 0.186-0.189")
