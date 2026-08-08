# p9_1024.py —— [[1024,1002,4]] 与 [[1024,912,8]] 符号级全量验证
# 目标：列互异、零简并、简并层结构、代表数分布、跨层伙伴、损失标度
import random, math, time
from itertools import combinations
from collections import Counter

random.seed(260807)

def build_cols(r, m):
    """CSS(RM(r,m)) 校验列：RM(r,m) 单项式在全部 2^m 点上的取值。
    列索引 = 点（整数 0..2^m-1，二进制 = F2^m 向量）。"""
    monos = []
    for size in range(r + 1):
        for comb in combinations(range(m), size):
            monos.append(comb)
    cols = []
    for x in range(2**m):
        col = 0
        for idx, mono in enumerate(monos):
            ok = 1
            for i in mono:
                if not (x >> i) & 1:
                    ok = 0
                    break
            if ok:
                col |= (1 << idx)
        cols.append(col)
    return cols, len(monos)

def syn_of_set(idx_set, cols):
    s = 0
    for i in idx_set:
        s ^= cols[i]
    return s

def f2_rank(vecs):
    basis = []
    for v in vecs:
        x = v
        for b in basis:
            if x ^ b < x:
                x ^= b
        if x:
            basis.append(x)
            basis.sort(key=lambda y: y.bit_length(), reverse=True)
    return len(basis)

def affine_span(A):
    """返回 (a0, span_set)：A 的仿射包（span_set = 差向量张成空间的全部元素）。"""
    a0 = A[0]
    vecs = [a ^ a0 for a in A[1:]]
    basis = []
    for v in vecs:
        x = v
        for b in basis:
            if x ^ b < x:
                x ^= b
        if x:
            basis.append(x)
            basis.sort(key=lambda y: y.bit_length(), reverse=True)
    span = {0}
    for b in basis:
        span |= {s ^ b for s in span}
    return a0, span

# ============ Part 1: [[1024, 1002, 4]] (r=1, d=4) ============
print("=== [[1024, 1002, 4]]  r=1, d=4  (C⊥=RM(8,10), min wt 4) ===")
m = 10
cols1, dim1 = build_cols(1, m)
n = len(cols1)
print(f"校验维数 dim RM(1,10) = {dim1}, n = {n}, k = {n - 2*dim1}")

t0 = time.time()
assert len(set(cols1)) == n
print(f"[1] 列互异: {n} 列全部唯一 ({time.time()-t0:.2f}s)  -> 权重1零简并 ✓")

# 权重2表（count）
t0 = time.time()
w2cnt = {}
for i in range(n):
    ci = cols1[i]
    for j in range(i + 1, n):
        s = ci ^ cols1[j]
        w2cnt[s] = w2cnt.get(s, 0) + 1
print(f"[2] 权重2表: {len(w2cnt)} syndrome ({time.time()-t0:.2f}s)")

dist2 = Counter()
for _ in range(5000):
    i, j = random.sample(range(n), 2)
    dist2[w2cnt[cols1[i] ^ cols1[j]]] += 1
print(f"[2] 权重2代表数分布(5000抽样): {dict(sorted(dist2.items()))}")
# 预期：全部 count=512（511个平行四边形伙伴 + 自身）

# 权重3跨层 → 权重1（伙伴 = 平行四边形补点 a⊕b⊕c）
t0 = time.time()
hit = 0
tot = 10000
for _ in range(tot):
    s = syn_of_set(random.sample(range(n), 3), cols1)
    if s in set(cols1):
        hit += 1
print(f"[3] 权重3跨层匹配权重1: {hit}/{tot} = {hit/tot:.6f} (闭式 1.0) ({time.time()-t0:.2f}s)")

ok3 = 0
for _ in range(2000):
    a, b, c = random.sample(range(n), 3)
    d = a ^ b ^ c
    if d in (a, b, c):
        continue
    if syn_of_set([a, b, c], cols1) == cols1[d]:
        ok3 += 1
print(f"[3] 权重3伙伴=补点实证: {ok3}/2000")

# 权重2失败率理论：最小权重解码随机选 → 失败率 = 1 - 1/512
print(f"[2] 权重2层失败率理论 = 511/512 = {511/512:.6f}")

# ============ Part 2: [[1024, 912, 8]] (r=2, d=8) ============
print()
print("=== [[1024, 912, 8]]  r=2, d=8  (C⊥=RM(7,10), min wt 8) ===")
cols2, dim2 = build_cols(2, m)
n2 = len(cols2)
print(f"校验维数 dim RM(2,10) = {dim2}, n = {n2}, k = {n2 - 2*dim2}")

t0 = time.time()
assert len(set(cols2)) == n2
print(f"[1] 列互异: {n2} 列全部唯一 ({time.time()-t0:.2f}s)")

# 权重1+2表
t0 = time.time()
w12 = set()
for i in range(n2):
    w12.add(cols2[i])
for i in range(n2):
    ci = cols2[i]
    for j in range(i + 1, n2):
        w12.add(ci ^ cols2[j])
print(f"[2] 权重≤2表: {len(w12)} syndrome ({time.time()-t0:.2f}s)")

t0 = time.time()
hit3 = 0
tot = 10000
for _ in range(tot):
    s = syn_of_set(random.sample(range(n2), 3), cols2)
    if s in w12:
        hit3 += 1
print(f"[2] 权重3零简并验证: {hit3}/{tot} 匹配 (预期 0, 差权重<8) ({time.time()-t0:.2f}s)")

# 权重4层：简并比例（rank≤3 判据，闭式=1）
t0 = time.time()
deg4 = 0
tot = 20000
for _ in range(tot):
    A = random.sample(range(n2), 4)
    a0 = A[0]
    if f2_rank([a ^ a0 for a in A[1:]]) <= 3:
        deg4 += 1
print(f"[3] 权重4层简并比例: {deg4}/{tot} = {deg4/tot:.6f} (闭式 1.0) ({time.time()-t0:.2f}s)")

# 权重4伙伴实证（仿射包=3 → 唯一3-平坦 → 伙伴=P\A）
ok4 = 0
try4 = 0
for _ in range(3000):
    A = random.sample(range(n2), 4)
    a0, span = affine_span(A)
    if len(span) != 8:
        continue
    P = {a0 ^ s for s in span}
    B = P - set(A)
    if len(B) == 4:
        try4 += 1
        if syn_of_set(B, cols2) == syn_of_set(A, cols2):
            ok4 += 1
print(f"[3] 权重4伙伴实证(仿射包=3): {ok4}/{try4}")

# 权重4退化比例（仿射包≤2 → 255个伙伴 → count=256）
deg2 = 0
tot = 20000
for _ in range(tot):
    A = random.sample(range(n2), 4)
    a0, span = affine_span(A)
    if len(span) <= 4:
        deg2 += 1
print(f"[3] 权重4退化(仿射包≤2)比例: {deg2}/{tot} = {deg2/tot:.6f} "
      f"(闭式 44,608,256/C(1024,4) = {44608256/45545029376:.6f})")

# 权重5层：简并比例（rank≤3 判据，闭式 P'_2(10) = 4.90e-3）
t0 = time.time()
deg5 = 0
tot = 2000000
for _ in range(tot):
    A = random.sample(range(n2), 5)
    a0 = A[0]
    if f2_rank([a ^ a0 for a in A[1:]]) <= 3:
        deg5 += 1
print(f"[4] 权重5层简并比例: {deg5}/{tot} = {deg5/tot:.8f} (闭式 4.898e-3) ({time.time()-t0:.2f}s)")

# 权重5伙伴实证：P\A（3点）
ok5 = 0
try5 = 0
for _ in range(300000):
    A = random.sample(range(n2), 5)
    a0, span = affine_span(A)
    if len(span) != 8:
        continue
    P = {a0 ^ s for s in span}
    B = P - set(A)
    if len(B) == 3:
        try5 += 1
        if syn_of_set(B, cols2) == syn_of_set(A, cols2):
            ok5 += 1
        if try5 >= 30:
            break
print(f"[4] 权重5伙伴实证(跨层→权重3): {ok5}/{try5}")

# ============ Part 3: 损失标度（分支级闭式） ============
print()
print("=== 损失标度（分支级） ===")
def loss_series(n, fails, theta):
    loss = 0.0
    for w, f in fails.items():
        loss += math.comb(n, w) * f * (theta / 2) ** (2 * w) * (1 - theta**2 / 4) ** (n - w)
    return loss

print("[[1024,1002,4]]: fail = {w1:0, w2:511/512, w3:1}  ->  loss ≈ c4·θ⁴ + c6·θ⁶")
for th in [0.001, 0.005, 0.01, 0.02]:
    l1 = loss_series(1024, {1: 0.0, 2: 511 / 512, 3: 1.0}, th)
    print(f"  θ={th}: loss={l1:.4e}  系数≈{l1/th**4:.3f} (θ⁴)")

print("[[1024,912,8]]: fail = {w1-3:0, w4:0.5005, w5:0.0049}  ->  loss ≈ c8·θ⁸ + c10·θ¹⁰")
for th in [0.01, 0.02, 0.05, 0.1]:
    l2 = loss_series(1024, {4: 0.5005, 5: 0.0049}, th)
    print(f"  θ={th}: loss={l2:.4e}  系数≈{l2/th**8:.3f} (θ⁸)")
