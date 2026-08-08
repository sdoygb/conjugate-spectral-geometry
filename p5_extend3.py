# p5_extend3.py —— 噪声验证最终修正
# Part C: [[64,20,8]] 注入 3/4/5 比特
# 失败判定（真实解码器语义）：
#   |S|<=3: 表内唯一 -> 成功
#   |S|=4: 唯一类 -> 成功; 简并类 -> 解码器选 dec4_rep（首代表），注入 != 首代表 -> 失败
#   |S|=5: syndrome 匹配 <=4 表 -> 解码选低权重代表 -> 残留逻辑 -> 失败; 否则按唯一权重5代表（内部简并另行抽样）

import itertools, time, random, math

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

def part_c():
    r, m = 2, 6
    n = 2 ** m
    rows = rm_rows(r, m)
    K = rm_rows(3, m)
    cols = eval_cols(rows, n)
    # 解码表权重 <= 3
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
    print(f'[C] 解码表（权重<=3）: {len(dec)} 项')

    # 权重 4 全量：syndrome -> (计数, 首代表)
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
    uniq4 = sum(1 for v in dec4_cnt.values() if v == 1)
    print(f'[C] 权重4全量: {tot4} 个, syndrome 唯一类={uniq4}, 简并类={len(dec4_cnt)-uniq4} '
          f'({time.time()-t0:.1f}s)')

    def in_C(x):
        for row in K:
            if parity_big(x & row, n):
                return False
        return True

    def run_injection(k_bits, n_trials, label):
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
                # 注入错误 χ_S
                chi = 0
                for i in range(k_bits):
                    if (mask >> i) & 1:
                        chi |= 1 << inj[i]
                # 解码 + 失败判定
                fail = False
                if w <= 3:
                    R = dec.get(sx, 0)
                    resid = chi ^ R
                    if resid != 0 and not in_C(resid):
                        fail = True
                elif w == 4:
                    cnt = dec4_cnt.get(sx, 0)
                    rep = dec4_rep.get(sx, 0)
                    if cnt == 1:
                        fail = False          # 唯一权重4代表 = chi
                    else:
                        fail = (chi != rep)   # 简并类：解码器选首代表
                else:  # w == 5
                    if sx in dec or sx in dec4_cnt:
                        fail = True           # 解码选 <=4 代表 -> 残留逻辑
                    # 不在表：按唯一权重5代表处理（内部简并单独抽样）
                tot_by_w[w] = tot_by_w.get(w, 0) + 1
                if fail:
                    fail_by_w[w] = fail_by_w.get(w, 0) + 1
        print(f'[C] {label}: 注入 {k_bits} 比特 × {n_trials} trials:')
        for w in sorted(tot_by_w):
            f = fail_by_w.get(w, 0)
            print(f'      |S|={w}: {f}/{tot_by_w[w]} ({100.0*f/tot_by_w[w]:.2f}%)')

    run_injection(3, 200, '[[64,20,8]]')
    run_injection(4, 200, '[[64,20,8]]')
    run_injection(5, 200, '[[64,20,8]]')

    # 权重 5 内部简并抽样：随机 20000 个权重5错误，检查 syndrome 与另一个权重5相同
    rng = random.Random(260807)
    seen5 = {}
    dup5 = 0
    for _ in range(20000):
        five = rng.sample(range(n), 5)
        sx = 0
        for i in five:
            sx ^= cols[i]
        if sx in seen5:
            dup5 += 1
        else:
            seen5[sx] = 1
    print(f'[C] 权重5内部简并抽样: {dup5}/20000 碰撞（含重复抽样估计）')

    # 损失标度：注入 4 比特的 theta^8 拟合（失败率 x sin^8）
    print('[C] 注入4比特损失标度（失败率 0.507 x sin^8(theta/2) 解析 + cos 因子）:')
    prev = None
    for th in [0.10, 0.15, 0.20, 0.30]:
        s2 = math.sin(th / 2) ** 2
        loss = 0.507 * (s2 ** 4) * (math.cos(th / 2) ** 8)  # 近似：|S|=4 项主导
        slope = ''
        if prev is not None:
            slope = f'{math.log(loss / prev) / math.log(th / 0.10):.2f}'
        prev = loss
        print(f'    theta={th:.2f}: loss~{loss:.3e}  斜率={slope}')

if __name__ == '__main__':
    part_c()
