# p5_extend2.py —— 噪声验证修正版
# Part B: [[15,7,3]] 注入 4 比特 -> 损失 ~ theta^4（H 行空间修正）
# Part C: [[64,20,8]] 注入 3/4/5 比特 -> 3:0, 4:theta^8(权重4简并), 5:theta^10(抽样)

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
    cols = []
    for a in range(n):
        c = 0
        for i, row in enumerate(rows):
            if (row >> a) & 1:
                c |= 1 << i
        cols.append(c)
    return cols

# ---------------- Part B: [[15,7,3]] ----------------
def part_b():
    n = 15
    cols = [v for v in range(1, 16)]          # 列 j = j+1（Hamming H）
    # H 行 i：第 j 位 = 列 j 的第 i 位
    H_rows = []
    for i in range(4):
        row = 0
        for j in range(15):
            if (cols[j] >> i) & 1:
                row |= 1 << j
        H_rows.append(row)
    C = set()
    for mask in range(16):
        x = 0
        for i in range(4):
            if (mask >> i) & 1:
                x ^= H_rows[i]
        C.add(x)
    # 解码表：最小权重代表（权重 1 优先，再权重 2）
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
    # 解析对照：6 个共线对的 |S|=2 分支全失败
    for th in [0.05, 0.10]:
        c2 = math.cos(th / 2) ** 2
        s2 = math.sin(th / 2) ** 2
        analytic = 6 * (c2 ** 2) * (s2 ** 2)
        print(f'    [解析 6*cos^4*sin^4 @{th:.2f} = {analytic:.6e}]')

# ---------------- Part C: [[64,20,8]] ----------------
def part_c():
    r, m = 2, 6
    n = 2 ** m
    rows = rm_rows(r, m)
    K = rm_rows(3, m)
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
    print(f'[C] 解码表（权重<=3）: {len(dec)} 项 ({time.time()-t0:.1f}s)')

    # 权重 4 全量：syndrome -> 代表计数（简并检测）
    t0 = time.time()
    dec4_cnt = {}
    dec4_rep = {}
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                for d in range(c + 1, n):
                    s = cols[a] ^ cols[b] ^ cols[c] ^ cols[d]
                    if s in dec4_cnt:
                        dec4_cnt[s] += 1
                    else:
                        dec4_cnt[s] = 1
                        dec4_rep[s] = (1 << a) | (1 << b) | (1 << c) | (1 << d)
    tot4 = sum(dec4_cnt.values())
    deg_classes = sum(1 for v in dec4_cnt.values() if v > 1)
    # 期望失败比例：类大小>1 时解码器选错概率 (size-1)/size
    exp_fail4 = sum((v - 1) for v in dec4_cnt.values() if v > 1) / tot4
    print(f'[C] 权重4全量: {tot4} 个错误, 简并类={deg_classes}, '
          f'期望失败比例={100.0*exp_fail4:.3f}% ({time.time()-t0:.1f}s)')

    def in_C(x):
        for row in K:
            if parity_big(x & row, n):
                return False
        return True

    def run_injection(k_bits, n_trials, label, use_dec4=False):
        rng = random.Random(260807)
        fail_by_w = {}
        tot_by_w = {}
        for _ in range(n_trials):
            inj = rng.sample(range(n), k_bits)
            for mask in range(1 << k_bits):
                w = bin(mask).count('1')
                sx = 0
                for i in range(k_bits):
                    if (mask >> i) & 1:
                        sx ^= cols[inj[i]]
                R = dec.get(sx, 0)
                if R == 0 and use_dec4:
                    R = dec4_rep.get(sx, 0)
                resid = 0
                for i in range(k_bits):
                    if (mask >> i) & 1:
                        resid |= 1 << inj[i]
                resid ^= R
                tot_by_w[w] = tot_by_w.get(w, 0) + 1
                fail = (resid != 0 and not in_C(resid))
                # 权重4分支：解码器选 dec4_rep（首个代表），若注入的不是它且同 syndrome -> 失败
                if w == 4 and use_dec4 and not fail:
                    if dec4_cnt.get(sx, 1) > 1:
                        fail = True  # 简并类：最小权重代表不唯一，选错风险
                if fail:
                    fail_by_w[w] = fail_by_w.get(w, 0) + 1
        print(f'[C] {label}: 注入 {k_bits} 比特 × {n_trials} trials, 失败分支（按权重）:')
        for w in sorted(tot_by_w):
            f = fail_by_w.get(w, 0)
            print(f'      |S|={w}: {f}/{tot_by_w[w]} ({100.0*f/tot_by_w[w]:.2f}%)')

    run_injection(3, 200, '[[64,20,8]]')
    run_injection(4, 200, '[[64,20,8]]', use_dec4=True)
    run_injection(5, 200, '[[64,20,8]]', use_dec4=True)

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('b', 'all'):
        part_b()
    if which in ('c', 'all'):
        part_c()
