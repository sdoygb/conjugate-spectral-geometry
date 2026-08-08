# p9c_1024.py —— r=3 家族成员 [[1024,672,16]] 验证
import random, math, time
from itertools import combinations

random.seed(260809)

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

m = 10
n = 2**m
print("=== [[1024, 672, 16]]  r=3, d=16 ===")
cols3, dim3 = build_cols(3, m)
print(f"dim RM(3,10) = {dim3}, k = {n - 2*dim3}")

t0 = time.time()
assert len(set(cols3)) == n
print(f"[1] 列互异: {n} 列全部唯一 ({time.time()-t0:.2f}s)")

t0 = time.time()
diff = 0
tot = 10000
for _ in range(tot):
    e7 = random.sample(range(n), 7)
    e6 = random.sample(range(n), 6)
    s7 = 0
    for i in e7: s7 ^= cols3[i]
    s6 = 0
    for i in e6: s6 ^= cols3[i]
    if s7 != s6:
        diff += 1
print(f"[2] 权重7 vs 权重6 syndrome 区分: {diff}/{tot} ({time.time()-t0:.2f}s)")

def gb(m, k):
    num = 1; den = 1
    for i in range(k):
        num *= 2**(m - i) - 1
        den *= 2**(k - i) - 1
    return num // den

def flats(m, k):
    return 2**(m - k) * gb(m, k)

C1024_8 = math.comb(1024, 8)
C1024_9 = math.comb(1024, 9)
E4_8 = math.comb(16, 8) - 2 * (2**4 - 1)
P3_10 = (flats(10, 4) * E4_8 + flats(10, 3)) / C1024_8
P3p_10 = flats(10, 4) * math.comb(16, 9) / C1024_9
print(f"[3] 权重8层简并比例闭式 P_3(10) = {P3_10:.4e}")
print(f"[3] 权重9层简并比例闭式 P'_3(10) = {P3p_10:.4e}")

t0 = time.time()
deg8 = 0
tot = 6000000
for _ in range(tot):
    A = random.sample(range(n), 8)
    a0 = A[0]
    if rank_upto([a ^ a0 for a in A[1:]], 4):
        deg8 += 1
print(f"[3] 权重8层抽样: {deg8}/{tot} = {deg8/tot:.2e} (闭式 {P3_10:.2e}) ({time.time()-t0:.2f}s)")

print()
print("=== [D] 1024 家族损失窗口（θ=0.01） ===")
c4 = math.comb(1024, 2) * (511/512) * (0.5)**4
c8 = math.comb(1024, 4) * 0.5005 * (0.5)**8
c16 = P3_10 * 0.5 * math.comb(1024, 8) * (0.5)**16
for name, cd, d in [("d=4", c4, 4), ("d=8", c8, 8), ("d=16", c16, 16)]:
    print(f"  [[1024,·,{d}]]: θ^d 系数 = {cd:.3e},  θ=0.01 损失 ≈ {cd*0.01**d:.2e}")
