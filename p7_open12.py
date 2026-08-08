# p7_open12.py —— 开放问题1（斯滕伯格精确常数）+ 开放问题2（权重 d/2+1 层）
# Part 1: 诊断 f2_rank vs 标准高斯消元 vs 精确公式（秩分布）
# Part 2: 权重 2^r+1 层简并比例 + 补集伙伴实证 + C⊥ 权重谱
import itertools, random, time

# ---------- rank 实现 A：贪心消元（10.32 用的原版） ----------
def rank_greedy(vecs):
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

# ---------- rank 实现 B：标准行阶梯消元（逐列主元） ----------
def rank_standard(vecs, m):
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

# ---------- 精确公式：n 个向量在 F2^m 中秩恰为 k 的概率 ----------
def p_rank_k(n, m, k):
    if k > min(n, m):
        return 0.0
    p = 2.0 ** (k * (n + m - k) - n * m)
    for i in range(k):
        p *= (1 - 2.0 ** (i - n)) * (1 - 2.0 ** (i - m)) / (1 - 2.0 ** (i - k))
    return p

def p_rank_le(n, m, k):
    return sum(p_rank_k(n, m, j) for j in range(k + 1))

# ---------- RM(r,m) 生成矩阵行 ----------
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

# ============================================================
# Part 1：秩分布诊断
# ============================================================
def part1():
    print("=" * 60)
    print("Part 1: 秩分布诊断（n=7 向量, F2^8）")
    print("=" * 60)
    n_vec, m_dim, N = 7, 8, 200000
    rng = random.Random(12345)

    # 1a. 独立均匀（允许零、重复）
    cnt_g = [0] * (m_dim + 1)
    cnt_s = [0] * (m_dim + 1)
    mismatch = 0
    for _ in range(N):
        vecs = [rng.getrandbits(m_dim) for _ in range(n_vec)]
        rg = rank_greedy(vecs)
        rs = rank_standard(vecs, m_dim)
        cnt_g[rg] += 1
        cnt_s[rs] += 1
        if rg != rs:
            mismatch += 1
    print(f"独立均匀样本 {N}：greedy vs standard 不一致 {mismatch}")
    print(f"  秩分布(greedy)  : {[cnt_g[k] for k in range(m_dim+1)]}")
    print(f"  秩分布(standard): {[cnt_s[k] for k in range(m_dim+1)]}")
    print("  公式(精确)      : " + " ".join(f"{p_rank_k(n_vec, m_dim, k):.5f}" for k in range(m_dim + 1)))
    p_le = p_rank_le(n_vec, m_dim, 4)
    print(f"  P(rank<=4) 公式 = {p_le:.6e} | standard 实测 = {cnt_s[0]+cnt_s[1]+cnt_s[2]+cnt_s[3]+cnt_s[4]:.0f}/{N} = {(cnt_s[0]+cnt_s[1]+cnt_s[2]+cnt_s[3]+cnt_s[4])/N:.6e}")

    # 1b. 无放回（8 点 → 7 差向量）——10.32 的真实抽样方式
    cnt_s2 = [0] * (m_dim + 1)
    for _ in range(N):
        A = rng.sample(range(2 ** m_dim), 8)
        vecs = [a ^ A[0] for a in A[1:]]
        cnt_s2[rank_standard(vecs, m_dim)] += 1
    print(f"无放回(8点)样本 {N}：P(rank<=4) = {sum(cnt_s2[:5])/N:.6e}（独立均匀公式 {p_le:.6e}）")
    print(f"  秩分布(standard): {[cnt_s2[k] for k in range(m_dim+1)]}")

# ============================================================
# Part 2：权重 d/2+1 层（权重 2^r+1）简并
# ============================================================
def part2():
    print("=" * 60)
    print("Part 2: 权重 2^r+1 层简并（θ^{d+2} 次主阶）")
    print("=" * 60)
    rng = random.Random(777)

    # ---- r=2, m=6：[[64,20,8]] 权重 5 层 ----
    r, m = 2, 6
    n = 2 ** m
    N = 200000
    hits = 0
    demo = []
    cnt = [0] * 7
    for _ in range(N):
        A = rng.sample(range(n), 2 ** r + 1)  # 5 点
        vecs = [a ^ A[0] for a in A[1:]]       # 4 差向量
        rk = rank_standard(vecs, m)
        cnt[rk] += 1
        if rk <= r + 1:
            hits += 1
            if len(demo) < 3:
                demo.append((A, rk))
    print(f"[r={r}, m={m}] 权重 {2**r+1} 层：简并比例 = {hits}/{N} = {hits/N:.6f}")
    print(f"  公式 P(rank<=3; n=4, m=6) = {p_rank_le(4, 6, 3):.6f}")
    print(f"  秩分布: {cnt}")

    # ---- r=3, m=8：[[256,70,16]] 权重 9 层 ----
    r, m = 3, 8
    n = 2 ** m
    N = 1000000
    hits = 0
    demo9 = []
    for _ in range(N):
        A = rng.sample(range(n), 2 ** r + 1)  # 9 点
        vecs = [a ^ A[0] for a in A[1:]]       # 8 差向量
        if rank_standard(vecs, m) <= r + 1:
            hits += 1
            if len(demo9) < 3:
                demo9.append(A)
    print(f"[r={r}, m={m}] 权重 {2**r+1} 层：简并比例 = {hits}/{N} = {hits/N:.6e}")
    print(f"  公式 P(rank<=4; n=8, m=8) = {p_rank_le(8, 8, 4):.6e}")

    # ---- 补集伙伴 syndrome 实证（r=3, m=8）----
    rows = rm_generator_rows(3, 8)
    dim = len(rows)
    cols = []
    for j in range(n):
        c = 0
        for i, row in enumerate(rows):
            if (row >> j) & 1:
                c |= 1 << i
        cols.append(c)
    print(f"RM(3,8) 列构造：dim={dim}, 列互异 = {len(set(cols)) == n}")

    def syndrome(pts):
        s = 0
        for e in pts:
            s ^= cols[e]
        return s

    # 对 demo9 中 rank<=4 的 9 子集：P = 仿射包(延拓) → B = P\A → syndrome 相等？
    ok = 0
    for A in demo9:
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
        while len(basis) < 4:
            for cand in range(n):
                x = cand
                for b in basis:
                    if x ^ b < x:
                        x ^= b
                if x:
                    basis.append(x)
                    break
        P = set()
        for combo in range(16):
            pt = A[0]
            for i, b in enumerate(basis):
                if (combo >> i) & 1:
                    pt ^= b
            P.add(pt)
        B = [p for p in P if p not in set(A)]
        if len(B) == 2 ** r - 1 and syndrome(A) == syndrome(B):
            ok += 1
    print(f"  补集伙伴实证（权重9→伙伴权重7）：{ok}/{len(demo9)} ✓")

    # ---- 权重 9 与权重 8 的 syndrome 区分（9+8=17 理论上不在 C⊥ 权重谱）----
    diff = 0
    for _ in range(2000):
        A9 = rng.sample(range(n), 9)
        A8 = rng.sample(range(n), 8)
        if syndrome(A9) != syndrome(A8):
            diff += 1
    print(f"  权重9 vs 权重8 syndrome 区分：{diff}/2000 ✓（预期全不同）")

    # ---- C⊥ = RM(4,8) 随机码字权重谱（低端）----
    rows4 = rm_generator_rows(4, 8)
    wcnt = {}
    for _ in range(20000):
        x = 0
        for row in rows4:
            if rng.random() < 0.5:
                x ^= row
        w = bin(x).count("1")
        wcnt[w] = wcnt.get(w, 0) + 1
    low = sorted(w for w in wcnt if w <= 40)
    print(f"  C⊥ 低权重谱（20000 随机码字）: " + " ".join(f"{w}:{wcnt[w]}" for w in low[:12]))
    has17 = any(w == 17 for w in wcnt)
    has18 = any(w == 18 for w in wcnt)
    print(f"  权重17存在: {has17} | 权重18存在: {has18}")

if __name__ == "__main__":
    t0 = time.time()
    part1()
    part2()
    print(f"\n总耗时 {time.time()-t0:.1f}s")
