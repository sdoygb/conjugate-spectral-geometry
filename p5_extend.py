# p5_extend.py —— 10.30 扩展：2048 比特可扩展性 + 噪声行为（零损失定理验证）
# Part A: m=11 (2048 比特) 列互异 + 简并抽样 + syndrome 抽样
# Part B: [[15,7,3]] 注入 4 比特相干旋转 -> 损失 ~ theta^4（对照）
# Part C: [[64,20,8]] 注入 4 比特 -> 损失=0；注入 5 比特 -> 标度

import itertools, time, random, sys, math

def parity_big(x, nbits):
    s = 1
    while s < nbits:
        x ^= x >> s
        s *= 2
    return x & 1

def rm_rows(r, m):
    n = 2 ** m
    rows = []
    for deg in range(r + 1):
        for S in itertools.combinations(range(m), deg):
            row = 0
            for v in range(n):
                if all((v >> i) & 1 for i in S):
                    row |= 1 << v
            rows.append(row)
    return rows

def eval_cols(rows, n):
    """列 a = 各行在 a 处的取值（syndrome 列）"""
    cols = []
    for a in range(n):
        c = 0
        for i, row in enumerate(rows):
            if (row >> a) & 1:
                c |= 1 << i
        cols.append(c)
    return cols

# ---------------- Part A: m=11 ----------------
def part_a():
    t_all = time.time()
    for (r, m) in [(2, 11), (3, 11), (4, 11)]:
        t0 = time.time()
        n = 2 ** m
        rows = rm_rows(r, m)
        dim = len(rows)
        k = n - 2 * dim
        d = 2 ** (r + 1)
        cols = eval_cols(rows, n)
        colset = set(cols)
        # (a) 列互异
        ok = len(colset) == n
        # (b) 跨权重简并抽样：XX 型 syndrome = col[a]^col[b]（常数位 0）vs 单比特（常数位 1）
        rng = random.Random(260807)
        bad_cross = 0
        for _ in range(200000):
            a, b = rng.sample(range(n), 2)
            s = cols[a] ^ cols[b]
            if s in colset:
                bad_cross += 1
        # (c) 内部简并抽样：权重 2 对的 syndrome 唯一性（去重抽样）
        bad_inner = 0
        seen = set()
        seen_pairs = set()
        for _ in range(400000):
            a, b = rng.sample(range(n), 2)
            key = (min(a, b), max(a, b))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            s = cols[a] ^ cols[b]
            if s in seen:
                bad_inner += 1
            seen.add(s)
        # (d) 随机权重 3..d-1 syndrome 抽样（完整 syndrome：X 部分 + Z 部分）
        gens = []
        for row in rows:
            gens.append((row, 0))
            gens.append((0, row))
        checked = 0
        for _ in range(2000):
            w = rng.randint(3, d - 1)
            X = 0
            for p in rng.sample(range(n), w):
                X |= 1 << p
            s = 0
            for i, (gx, gz) in enumerate(gens):
                if parity_big(X & gz, n):
                    s |= 1 << i
            if s == 0:
                checked = -1
                break
            checked += 1
        print(f'[A] RM({r},{m}) [[{n},{k},{d}]] dim={dim}: '
              f'列互异={"✓" if ok else "✗"} 跨权重简并抽样={bad_cross}/200000 '
              f'内部简并抽样={bad_inner}/{len(seen_pairs)} syndrome抽样={checked}/2000 '
              f'({time.time()-t0:.1f}s)')
    print(f'[A] 总计 {time.time()-t_all:.1f}s')

# ---------------- Part B: [[15,7,3]] 4 比特注入 theta^4 ----------------
def part_b():
    n = 15
    # H: 4x15，列 = 1..15
    cols = [v for v in range(1, 16)]
    # C = H 行空间（16 个码字）
    C = set()
    for mask in range(16):
        x = 0
        for i in range(4):
            if (mask >> i) & 1:
                x |= 1 << i
        C.add(x)
    # 解码表：syndrome -> 最小权重代表
    dec = {0: 0}
    for i in range(n):
        dec[cols[i]] = 1 << i
    for a in range(n):
        for b in range(a + 1, n):
            s = cols[a] ^ cols[b]
            if s not in dec:
                dec[s] = (1 << a) | (1 << b)
    inj = [0, 1, 2, 3]
    print('[B] [[15,7,3]] 注入 4 比特相干旋转：损失 vs theta')
    print('    theta      损失        斜率(log-log)')
    prev = None
    for th in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        c2 = math.cos(th / 2) ** 2
        s2 = math.sin(th / 2) ** 2
        loss = 0.0
        for mask in range(16):
            w = bin(mask).count('1')
            coef2 = (c2 ** (4 - w)) * (s2 ** w)
            sx = 0
            for i in range(4):
                if (mask >> i) & 1:
                    sx ^= cols[inj[i]]
            R = dec.get(sx, 0)
            resid = 0
            for i in range(4):
                if (mask >> i) & 1:
                    resid |= 1 << inj[i]
            resid ^= R
            if resid not in C:
                loss += coef2
        slope = ''
        if prev is not None:
            slope = f'{math.log(loss / prev) / math.log(th / 0.05):.2f}'
        prev = loss
        print(f'    {th:.2f}      {loss:.6e}     {slope}')

# ---------------- Part C: [[64,20,8]] 零损失 vs 5 比特标度 ----------------
def part_c():
    r, m = 2, 6
    n = 2 ** m
    rows = rm_rows(r, m)          # C = RM(2,6)，22 行
    K = rm_rows(3, m)             # C^⊥ = RM(3,6)，42 行（核对矩阵）
    cols = eval_cols(rows, n)
    # 解码表：权重 <= 3
    t0 = time.time()
    dec = {0: 0}
    for i in range(n):
        dec[cols[i]] = 1 << i
    for a in range(n):
        for b in range(a + 1, n):
            s = cols[a] ^ cols[b]
            if s not in dec:
                dec[s] = (1 << a) | (1 << b)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                s = cols[a] ^ cols[b] ^ cols[c]
                if s not in dec:
                    dec[s] = (1 << a) | (1 << b) | (1 << c)
    print(f'[C] 解码表构建（权重<=3）: {len(dec)} 项 ({time.time()-t0:.1f}s)')

    def in_C(x):
        for row in K:
            if parity_big(x & row, n):
                return False
        return True

    def run_injection(k_bits, n_trials, label):
        rng = random.Random(260807)
        fail_branches = 0
        tot_branches = 0
        for _ in range(n_trials):
            inj = rng.sample(range(n), k_bits)
            for mask in range(1 << k_bits):
                sx = 0
                for i in range(k_bits):
                    if (mask >> i) & 1:
                        sx ^= cols[inj[i]]
                R = dec.get(sx, 0)
                resid = 0
                for i in range(k_bits):
                    if (mask >> i) & 1:
                        resid |= 1 << inj[i]
                resid ^= R
                tot_branches += 1
                if not in_C(resid):
                    fail_branches += 1
        print(f'[C] {label}: 注入 {k_bits} 比特 × {n_trials} trials × {1<<k_bits} 分支 = {tot_branches} 分支, '
              f'恢复失败分支 = {fail_branches} ({100.0*fail_branches/tot_branches:.3f}%)')

    run_injection(4, 200, '[[64,20,8]]')
    run_injection(5, 200, '[[64,20,8]]')

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('a', 'all'):
        part_a()
    if which in ('b', 'all'):
        part_b()
    if which in ('c', 'all'):
        part_c()
