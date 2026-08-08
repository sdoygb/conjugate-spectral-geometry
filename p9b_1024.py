# p9b_1024.py —— 补充确认：权重5层大样本、r=1方向结构（快）
import random, math, time
from itertools import combinations

random.seed(260808)

def build_cols(r, m):
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

def rank_upto(vecs, cap):
    """秩是否 ≤ cap（提前终止）"""
    basis = []
    for v in vecs:
        x = v
        for b in basis:
            if x ^ b < x:
                x ^= b
        if x:
            basis.append(x)
            if len(basis) > cap:
                return False
            basis.sort(key=lambda y: y.bit_length(), reverse=True)
    return True

# ============ [A] 权重5层大样本（r=2, m=10） ============
print("=== [A] 权重5层简并比例 大样本 ===")
m = 10
n = 2**m
t0 = time.time()
deg5 = 0
tot = 6000000
for _ in range(tot):
    A = random.sample(range(n), 5)
    a0 = A[0]
    if rank_upto([a ^ a0 for a in A[1:]], 3):
        deg5 += 1
print(f"权重5层: {deg5}/{tot} = {deg5/tot:.8f} (闭式 4.8976e-3) ({time.time()-t0:.2f}s)")
print(f"合并(2e6+6e6): {(9571+deg5)}/8000000 = {(9571+deg5)/8000000:.8f} (闭式 4.8976e-3)")

# ============ [B] r=1 方向结构 ============
print()
print("=== [B] r=1 权重2 syndrome = 方向结构 ===")
cols1, dim1 = build_cols(1, m)
ok_dir = 0
tot = 20000
for _ in range(tot):
    i, j = random.sample(range(n), 2)
    s = cols1[i] ^ cols1[j]
    if (s >> 1) == (i ^ j) and (s & 1) == 0:
        ok_dir += 1
print(f"方向结构验证: {ok_dir}/{tot} (syndrome = (0, x_i⊕x_j))")
syn_set = set()
for i in range(n):
    for j in range(i + 1, n):
        syn_set.add(cols1[i] ^ cols1[j])
print(f"权重2 syndrome 总数 = {len(syn_set)} (预期 2^10 - 1 = 1023)")
