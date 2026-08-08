# -*- coding: utf-8 -*-
"""mix_channel.py —— 混合通道闭式探索（深挖①：随机 Pauli + 相干）

模型（10.36 同款）：RM(1,4) CSS 码 [[16,6,4]]（10.36 四档中最小的 d=4 档）
每比特独立噪声：
  - 相干 Z 旋转 R_Z(θ)（确定性，全部比特同角）
  - 随机 Z-flip：Bernoulli(p)（与旋转对易，顺序无关）
有效单比特通道：ρ → (1-p)·R_θρR_θ† + p·ZR_θρR_θ†Z

态矢量模拟（n=16，|0_L⟩ = Σ_{x∈RM(2,4)}|x⟩/√2048，2048 个分量）：
  ψ'(x) = e^{iθ(wt(x)-8)}·(-1)^{F·x}/√2048
X-syndrome 类投影（32 类，X-stab 群 32 元素，相位 (-1)^{s·a(g)} 用基系数）+
min-weight Z 型恢复 + 逻辑 Z 测量 → loss_Z = Σ_s (‖ψ'_s‖² - |⟨0_L|R_sψ'_s⟩|²)

输出：loss(p, θ) 网格 + 各 p 下 log-log 斜率（θ 标度）+ 各 θ 下 p 标度
"""
import itertools
import numpy as np

# ---------------- RM 码构造 ----------------
def rm_rows(r, m):
    """RM(r,m) 生成矩阵行：单项式（次数≤r）在全部 2^m 点上的值"""
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

def build_rm_css(r, m):
    """RM(r,m) CSS 码 [[n, k, 2^{r+1}]]：X/Z-stab 生成元（行空间 RM(r,m)）"""
    n = 2 ** m
    rows = rm_rows(r, m)
    rc = len(rows)
    k = n - 2 * rc
    d = 2 ** (r + 1)
    return dict(n=n, k=k, d=d, rows=rows, rc=rc)

def rm_codewords(m, r):
    """RM(r,m) 全部码字（2^dim 个）"""
    rows = rm_rows(r, m)
    words = [0]
    for row in rows:
        words += [w ^ row for w in words]
    return words

def syndrome_of_zflip(F, rows):
    """Z 型错误（flip 集 F）的 X-syndrome：s_i = F·g_i mod 2"""
    s = 0
    for i, g in enumerate(rows):
        if bin(F & g).count('1') & 1:
            s |= 1 << i
    return s

def build_recovery_table(rows, n):
    """min-weight Z 型恢复表：X-syndrome → (恢复 flip 集, 权重)
    权重 1..3 全枚举（16+120+560=696）；缺失类（min weight ≥4 = 逻辑类）
    补恢复 I（权重 0）——该类无法纠正，loss 全额计入"""
    table = {}
    for w in (1, 2, 3):
        for comb in itertools.combinations(range(n), w):
            F = 0
            for j in comb:
                F |= 1 << j
            s = syndrome_of_zflip(F, rows)
            if s not in table:
                table[s] = (F, w)
    table[0] = (0, 0)
    for s in range(1 << len(rows)):
        if s not in table:
            table[s] = (0, 0)
    return table

def x_stab_group(rows):
    """X-stab 群元素（2^rc 个）+ 基系数 a(g)（生成元基下的 rc 位向量）
    类投影相位 = (-1)^{s·a(g)}——a(g) 是基系数，不是 flip 集 g 本身"""
    group = [0]
    coefs = [0]
    for i, row in enumerate(rows):
        ng = [g ^ row for g in group]
        nc = [c | (1 << i) for c in coefs]
        group += ng
        coefs += nc
    return group, coefs

# ---------------- 模拟 ----------------
def simulate_many(rows, n, theta, p, n_trials, seed=260807):
    """扫描一个 (θ, p)：n_trials 次 flip realization 平均 loss"""
    rng = np.random.default_rng(seed)
    cw = rm_codewords(4, 2)          # RM(2,4) 码字（2048）
    idx = {x: i for i, x in enumerate(cw)}
    N = len(cw)
    amp0 = np.full(N, 1.0 / np.sqrt(N), dtype=complex)
    wt = np.array([bin(x).count('1') for x in cw], dtype=float)
    group, coefs = x_stab_group(rows)
    G = len(group)
    table = build_recovery_table(rows, n)
    # X_g 置换索引
    perm = np.zeros((N, G), dtype=np.int64)
    for gi, g in enumerate(group):
        for xi, x in enumerate(cw):
            perm[xi, gi] = idx[x ^ g]
    s_list = sorted(table.keys())
    rec_vec = {}
    for s in s_list:
        R, _ = table[s]
        rec_vec[s] = np.array([-1.0 if (bin(R & x).count('1') & 1) else 1.0
                               for x in cw])
    # 类投影相位 (-1)^{s·a(g)}
    sg_phase = np.zeros((len(s_list), G), dtype=complex)
    for si, s in enumerate(s_list):
        for gi, a in enumerate(coefs):
            sg_phase[si, gi] = 1.0 if (bin(s & a).count('1') & 1) == 0 else -1.0
    losses = []
    for _ in range(n_trials):
        bits = rng.random(n) < p
        F = 0
        for j, b in enumerate(bits):
            if b:
                F |= 1 << j
        fx = np.array([-1.0 if (bin(F & x).count('1') & 1) else 1.0
                       for x in cw])
        psi = amp0 * np.exp(1j * theta * (wt - n / 2)) * fx
        psiG = psi[perm]                      # (N, G)
        loss = 0.0
        for si, s in enumerate(s_list):
            ps = psiG @ sg_phase[si] / G      # P_s ψ'（N 维）
            norm2 = np.vdot(ps, ps).real
            if norm2 < 1e-30:
                continue
            ov = np.vdot(rec_vec[s] * amp0, ps)   # ⟨0_L|R_s ψ'_s⟩（未归一化）
            loss += norm2 - abs(ov) ** 2       # 类概率 - 恢复到|0_L⟩概率
        losses.append(loss)
    return float(np.mean(losses))

def main():
    r, m = 1, 4
    code = build_rm_css(r, m)
    n, rows = code['n'], code['rows']
    print(f'码: RM({r},{m}) CSS [[{n},{code["k"]},{code["d"]}]]  n={n}')
    thetas = [0.02, 0.04, 0.06, 0.08, 0.10]
    ps = [0.0, 1e-4, 1e-3, 3e-3, 1e-2, 3e-2, 0.1]
    N_TRIALS = 300
    print(f'\nloss(p, θ) 网格（{N_TRIALS} trials/点）：')
    print('p       ' + ''.join(f'θ={t:<7.2f}' for t in thetas))
    grid = {}
    for p in ps:
        row = []
        for th in thetas:
            L = simulate_many(rows, n, th, p, N_TRIALS)
            grid[(p, th)] = L
            row.append(f'{L:.3e}')
        print(f'{p:<8.3g}' + ' '.join(f'{v:<12}' for v in row))
    print('\n--- θ 标度（固定 p 的 log-log 斜率）---')
    lt = np.log(thetas)
    for p in ps:
        y = np.log([max(grid[(p, th)], 1e-16) for th in thetas])
        slope, _ = np.polyfit(lt, y, 1)
        print(f'  p={p:<6g}: 斜率 = {slope:.3f}')
    print('\n--- p 标度（固定 θ 的 log-log 斜率，p ∈ [1e-4, 0.1]）---')
    lp = np.log([p for p in ps if p > 0])
    for th in thetas:
        y = np.log([max(grid[(p, th)], 1e-16) for p in ps if p > 0])
        slope, _ = np.polyfit(lp, y, 1)
        print(f'  θ={th:<6g}: 斜率 = {slope:.3f}')
    L0 = grid[(0.0, 0.02)]
    c4 = L0 / 0.02 ** 4
    print(f'\n纯相干 θ=0.02: loss = {L0:.3e}，c_4 = {c4:.3e}'
          f'（10.36 表 2.0e-3，c_4≈1.25e4）')

if __name__ == '__main__':
    main()
