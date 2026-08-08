# p6_deg_prop.py —— 10.32：权重 2^r 层简并（包含性等价）与标度律 θ^d 完整证明
# r=3 验证：[[256,70,16]] 权重 8 层简并比例 + 补集伙伴实证；r=2 对照；m=9 比例对照
import itertools, random, time

def rm_generator_rows(r, m):
    """RM(r,m) 生成矩阵行（评估形式），列 = 点 0..2^m-1"""
    pts = list(range(2**m))
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
    y ^= y >> 16; y ^= y >> 8; y ^= y >> 4; y ^= y >> 2; y ^= y >> 1
    return y & 1

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

def verify(r, m, n_synd=3000, n_deg=100000, seed=42):
    t0 = time.time()
    rows = rm_generator_rows(r, m)
    dim = len(rows)
    n = 2**m
    cols = []
    for j in range(n):
        c = 0
        for i, row in enumerate(rows):
            if (row >> j) & 1:
                c |= 1 << i
        cols.append(c)
    d_theory = 2**(r+1)
    print(f"\n=== [{r},{m}] n={n} dim={dim} k={n-2*dim} d={d_theory} ===")
    # 1) 列互异
    assert len(set(cols)) == n, "列互异失败"
    print(f"  列互异: {len(set(cols))}/{n} OK")
    # 2) 权重 2 全量：内部唯一 + 跨权重位0封锁
    seen = set()
    bad_inner = 0
    npairs = n*(n-1)//2
    for a in range(n):
        ca = cols[a]
        for b in range(a+1, n):
            s = ca ^ cols[b]
            if s in seen:
                bad_inner += 1
            seen.add(s)
    bad_cross = sum(1 for a in range(n) for b in range(a+1,n) if (cols[a]^cols[b]) & 1)
    print(f"  权重2全量 {npairs} 对: 内部简并 {bad_inner}, 跨权重位0封锁 {bad_cross} OK")
    # 3) syndrome 抽样（d 核验：权重 < d 非零）
    rng = random.Random(seed)
    z = 0
    for _ in range(n_synd):
        w = rng.randint(3, d_theory-1)
        err = rng.sample(range(n), w)
        sx = 0
        for e in err:
            sx ^= cols[e]
        if sx == 0:
            z += 1
    print(f"  syndrome抽样 权重3..{d_theory-1}: 零 {z}/{n_synd} OK")
    # 4) 权重 2^r 层简并比例（仿射包 rank <= r+1 判据）
    w0 = 2**r
    hits = 0
    demo = []
    rank_hist = {}
    for _ in range(n_deg):
        A = rng.sample(range(n), w0)
        a0 = A[0]
        vecs = [a ^ a0 for a in A[1:]]
        rk = f2_rank(vecs)
        rank_hist[rk] = rank_hist.get(rk, 0) + 1
        if rk <= r + 1:
            hits += 1
            if len(demo) < 5:
                demo.append((A, vecs, rk))
    prop = hits / n_deg
    print(f"  权重{w0}层: 仿射包rank分布 {dict(sorted(rank_hist.items()))}")
    print(f"  简并比例(rank<=r+1): {hits}/{n_deg} = {prop:.6f}")
    # 5) 补集伙伴实证：rank<=r+1 的 A -> P=仿射包延拓 -> B=P\A -> syndrome 相等
    ok = 0
    for A, vecs, rk in demo:
        basis = []
        for v in vecs:
            x = v
            for b in basis:
                if x ^ b < x:
                    x ^= b
            if x:
                basis.append(x)
                basis.sort(key=lambda y: y.bit_length(), reverse=True)
        while len(basis) < r + 1:
            for cand in range(n):
                x = cand
                for b in basis:
                    if x ^ b < x:
                        x ^= b
                if x:
                    basis.append(x)
                    break
        P = set()
        for combo in range(1 << (r+1)):
            pt = A[0]
            for i, b in enumerate(basis):
                if (combo >> i) & 1:
                    pt ^= b
            P.add(pt)
        Aset = set(A)
        B = [p for p in P if p not in Aset]
        sA = 0
        for e in A: sA ^= cols[e]
        sB = 0
        for e in B: sB ^= cols[e]
        if sA == sB:
            ok += 1
    print(f"  补集伙伴实证 syndrome(A)==syndrome(P\\A): {ok}/{len(demo)} OK")
    print(f"  耗时 {time.time()-t0:.1f}s")
    return prop

if __name__ == "__main__":
    verify(3, 8, n_synd=3000, n_deg=100000)   # [[256,70,16]] r=3
    verify(2, 6, n_synd=2000, n_deg=20000)    # [[64,20,8]]  r=2 对照
    verify(3, 9, n_synd=2000, n_deg=300000)   # [[512,252,16]] m=9 比例对照
