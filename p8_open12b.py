# p8_open12b.py —— 开放问题1/2 的精确闭式验证 + 权重 d/2+1 层失败率
import itertools, random, time
from math import comb

# ---------- 组合闭式 ----------
def gaussian_binom(m, k):
    num, den = 1, 1
    for i in range(k):
        num *= 2 ** (m - i) - 1
        den *= 2 ** (k - i) - 1
    return num // den

def flats(m, k):
    """AG(m,2) 中 k-平坦数 = 2^{m-k}·[m choose k]_2"""
    return 2 ** (m - k) * gaussian_binom(m, k)

def E_aff(k, s):
    """固定 k-平坦内仿射包恰为 k 维的 s 点子集数"""
    if s > 2 ** k:
        return 0
    if s > 2 ** (k - 1):
        return comb(2 ** k, s)  # 装不进任何 (k-1)-平坦
    total = comb(2 ** k, s)
    for j in range(k):
        total -= flats(k, j) * E_aff(j, s)
    return total

def P_r(m, r):
    """权重 2^r 层简并比例（闭式）"""
    s = 2 ** r
    num = flats(m, r + 1) * E_aff(r + 1, s) + flats(m, r)
    return num / comb(2 ** m, s)

def P_prime_r(m, r):
    """权重 2^r+1 层简并比例（闭式）：s > 2^r 自动仿射包 = r+1"""
    s = 2 ** r + 1
    return flats(m, r + 1) * comb(2 ** (r + 1), s) / comb(2 ** m, s)

# ---------- RM 列 ----------
def rm_generator_rows(r, m):
    pts = list(range(2 ** m))
    rows = []
    for deg in range(r + 1):
        for mono in itertools.combinations(range(m), deg):
            row = 0
            for j, pt in enumerate(pts):
                v = 1
                for i in mono:
                    if not (pt >> i) & 1:
                        v = 0
                        break
                if v:
                    row |= 1 << j
            rows.append(row)
    return rows

def parity_big(x):
    y = 0
    while x:
        y ^= x & 0xFFFFFFFF
        x >>= 32
    y ^= y >> 16
    y ^= y >> 8
    y ^= y >> 4
    y ^= y >> 2
    y ^= y >> 1
    return y & 1

def rank_std(vecs, m):
    rows = list(vecs)
    r = 0
    for col in range(m):
        piv = None
        for i in range(r, len(rows)):
            if (rows[i] >> col) & 1:
                piv = i
                break
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for i in range(len(rows)):
            if i != r and (rows[i] >> col) & 1:
                rows[i] ^= rows[r]
        r += 1
    return r

def syndrome_of(pts, cols):
    s = 0
    for e in pts:
        s ^= cols[e]
    return s

# ============ Part A：闭式表 ============
print("=" * 66)
print("Part A: 组合闭式 P_r(m) 与 P'_r(m) 数值表")
print("=" * 66)
print(f"{'r':>2} {'m':>3} {'P_r(权重2^r层)':>16} {'P_r(m)全简并?':>12} {'P_r(2^r+1层)':>16}")
for r in (1, 2, 3):
    for m in (6, 7, 8, 9, 10):
        if 2 ** m < 2 ** (r + 1) + 2:
            continue
        p = P_r(m, r)
        pp = P_prime_r(m, r)
        print(f"{r:>2} {m:>3} {p:>16.8e} {str(p > 0.999999):>12} {pp:>16.8e}")

# ============ Part B：权重 5 层直接验证（[[64,20,8]]）============
print("\n" + "=" * 66)
print("Part B: [[64,20,8]] 权重 5 层——rank 判据 vs syndrome 匹配 vs 闭式")
print("=" * 66)
r, m = 2, 6
n = 2 ** m
rows = rm_generator_rows(r, m)
cols = []
for j in range(n):
    c = 0
    for i, row in enumerate(rows):
        if (row >> j) & 1:
            c |= 1 << i
    cols.append(c)

# 构建权重 <= 4 的 syndrome 表（最小权重代表）
t0 = time.time()
dec = {}   # syndrome -> 权重
for w in range(0, 5):
    for sub in itertools.combinations(range(n), w):
        sx = 0
        for e in sub:
            sx ^= cols[e]
        if sx not in dec:
            dec[sx] = w
print(f"权重<=4 表构建: {len(dec)} syndrome, {time.time()-t0:.1f}s")

rng = random.Random(2024)
N = 200000
hits_rank = 0
hits_synd = 0
match_w3 = 0
for _ in range(N):
    A = rng.sample(range(n), 5)
    vecs = [a ^ A[0] for a in A[1:]]
    if rank_std(vecs, m) <= 3:
        hits_rank += 1
    sx = syndrome_of(A, cols)
    if sx in dec:
        hits_synd += 1
        if dec[sx] <= 3:
            match_w3 += 1
print(f"权重5层: rank判据 {hits_rank}/{N} = {hits_rank/N:.6f}")
print(f"          syndrome匹配<=4表 {hits_synd}/{N} = {hits_synd/N:.6f}（其中代表权重<=3: {match_w3}）")
print(f"          闭式 P'_2(6) = {P_prime_r(6, 2):.6f}")

# 补集伙伴实证（rank<=3 的 5 子集 → P = 3-平坦 → B = P\A 3 点）
demo = 0
ok = 0
for _ in range(200000):
    A = rng.sample(range(n), 5)
    vecs = [a ^ A[0] for a in A[1:]]
    basis = []
    for v in vecs:
        x = v
        for b in basis:
            if x ^ b < x:
                x ^= b
        if x:
            basis.append(x)
            basis.sort(key=lambda y: y.bit_length(), reverse=True)
    if len(basis) <= 3:
        demo += 1
        while len(basis) < 3:
            for cand in range(n):
                x = cand
                for b in basis:
                    if x ^ b < x:
                        x ^= b
                if x:
                    basis.append(x)
                    break
        P = set()
        for combo in range(8):
            pt = A[0]
            for i, b in enumerate(basis):
                if (combo >> i) & 1:
                    pt ^= b
            P.add(pt)
        B = [p for p in P if p not in set(A)]
        if len(B) == 3 and syndrome_of(A, cols) == syndrome_of(B, cols):
            ok += 1
        if demo >= 30:
            break
print(f"  补集伙伴实证（权重5→伙伴权重3）: {ok}/{demo} ✓")

# ============ Part C：权重 9 层补样本（[[256,70,16]]）============
print("\n" + "=" * 66)
print("Part C: [[256,70,16]] 权重 9 层——补样本")
print("=" * 66)
r, m = 3, 8
n = 2 ** m
N = 4000000
hits = 0
for _ in range(N):
    A = rng.sample(range(n), 9)
    vecs = [a ^ A[0] for a in A[1:]]
    if rank_std(vecs, m) <= 4:
        hits += 1
print(f"权重9层: rank判据 {hits}/{N} = {hits/N:.6e}（闭式 P'_3(8) = {P_prime_r(8, 3):.6e}）")
