# -*- coding: utf-8 -*-
"""mix_enumerate.py —— 混合通道闭式的错误模式枚举（精确，无 Monte Carlo 噪声）

loss(p, θ) = Σ_{F} p^{|F|}(1-p)^{16-|F|}·loss(F, θ)
权重 ≤ 3 的 flip 集全枚举（696 个，确定性 loss），权重 ≥ 4 截断 O(p⁴)。

验证锚点（纯随机 θ=0，解析闭式）：
  权重 1：loss = 0（完美恢复）
  权重 2：loss = 7/8（15 类 × 8 成员，恢复表选 1 个，其余 7 个误恢复 → 权重 4 逻辑）
  权重 3：loss = 1（每类含单比特成员，恢复后残留权重 4 逻辑）
  → loss_rand(p) = 105·p²(1-p)^14 + 560·p³(1-p)^13 + O(p⁴)
"""
import itertools
import numpy as np
from mix_channel import (rm_rows, rm_codewords, x_stab_group,
                         build_recovery_table, syndrome_of_zflip)

# ---------------- 确定性 loss(F, θ) ----------------
def build_env(r, m):
    """环境：码字索引、X-stab 群、恢复表、置换表"""
    rows = rm_rows(r, m)
    n = 2 ** m
    cw = rm_codewords(m, 2)              # RM(2,m) 码字（|0_L⟩ 支撑）
    idx = {x: i for i, x in enumerate(cw)}
    N = len(cw)
    amp0 = np.full(N, 1.0 / np.sqrt(N), dtype=complex)
    wt = np.array([bin(x).count('1') for x in cw], dtype=float)
    group, coefs = x_stab_group(rows)
    G = len(group)
    table = build_recovery_table(rows, n)
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
    sg_phase = np.zeros((len(s_list), G), dtype=complex)
    for si, s in enumerate(s_list):
        for gi, a in enumerate(coefs):
            sg_phase[si, gi] = 1.0 if (bin(s & a).count('1') & 1) == 0 else -1.0
    return dict(rows=rows, n=n, cw=cw, idx=idx, N=N, amp0=amp0, wt=wt,
                group=group, G=G, table=table, perm=perm,
                s_list=s_list, rec_vec=rec_vec, sg_phase=sg_phase)

def loss_for_F(env, theta, F, base_theta=None):
    """确定性 loss：flip 集 F + 相干 θ（min-weight 解码 + 逻辑 Z 测量）
    向量化：一次矩阵乘算全部 32 类的投影 PS = psi[perm] @ sg_phase.T / G"""
    n, N = env['n'], env['N']
    amp0, wt = env['amp0'], env['wt']
    perm, G = env['perm'], env['G']
    s_list, rec_vec, sg_phase = env['s_list'], env['rec_vec'], env['sg_phase']
    if base_theta is None:
        base_theta = amp0 * np.exp(1j * theta * (wt - n / 2))
    fx = np.array([-1.0 if (bin(F & x).count('1') & 1) else 1.0
                   for x in env['cw']])
    psi = base_theta * fx
    PS = psi[perm] @ sg_phase.T / G          # (N, n_s) 全部类投影
    norm2 = np.abs(PS) ** 2                  # (N, n_s)
    norms = norm2.sum(axis=0)                # (n_s,) 每类概率
    ov = np.zeros(len(s_list), dtype=complex)
    for si, s in enumerate(s_list):
        ov[si] = np.vdot(rec_vec[s] * amp0, PS[:, si])
    return float((norms - np.abs(ov) ** 2).sum())

def loss_grid(env, thetas, ps, max_w=3):
    """枚举权重 ≤ max_w 的 flip 集 → loss(p, θ) 网格（O(p^{max_w+1}) 截断）"""
    n = env['n']
    flips = {0: [(0, 1.0)]}              # w -> [(F, loss(F,θ) for θ=0? no...]
    # 对每个 (F, θ) 算 loss
    print(f'枚举权重 ≤ {max_w} 的 flip 集（含 θ 依赖）...')
    per_w = {}
    for w in range(max_w + 1):
        combos = [0] if w == 0 else [sum(1 << j for j in c)
                                     for c in itertools.combinations(range(n), w)]
        per_w[w] = combos
    print(f'  权重分布: ' + ', '.join(f'w{w}={len(per_w[w])}' for w in per_w))
    grid = {}
    for th in thetas:
        base_theta = env['amp0'] * np.exp(1j * th * (env['wt'] - n / 2))
        cache = {F: loss_for_F(env, th, F, base_theta) for w, combos in per_w.items() for F in combos}
        for p in ps:
            total = 0.0
            for w, combos in per_w.items():
                coef = p ** w * (1 - p) ** (n - w)
                for F in combos:
                    total += coef * cache[F]
            grid[(p, th)] = total
    return grid

def main():
    r, m = 1, 4
    env = build_env(r, m)
    n = env['n']
    print(f'码: RM({r},{m}) CSS [[{n}, {n-2*len(env["rows"])}, 4]]  '
          f'|0_L⟩ 分量 {env["N"]}，类数 {len(env["s_list"])}')
    # 纯随机 θ=0：验证解析闭式
    print('\n=== 纯随机 θ=0：枚举 vs 解析 ===')
    for p in [1e-4, 1e-3, 3e-3, 1e-2, 3e-2, 0.1]:
        L = loss_grid(env, [0.0], [p])
        analytic = (105 * p ** 2 * (1 - p) ** 14 +
                    560 * p ** 3 * (1 - p) ** 13)
        print(f'  p={p:<6g} 枚举={L[(p,0.0)]:.4e}  解析={analytic:.4e}  比={L[(p,0.0)]/analytic:.4f}')
    # 混合网格
    thetas = [0.0, 0.01, 0.02, 0.05, 0.10]
    ps = [0.0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 0.1]
    print('\n=== loss(p, θ) 网格（枚举，O(p⁴) 截断）===')
    grid = loss_grid(env, thetas, ps)
    print('p       ' + ''.join(f'θ={t:<6.2f}' for t in thetas))
    for p in ps:
        print(f'{p:<8.3g}' + ' '.join(f'{grid[(p,t)]:.3e}' for t in thetas))
    # 标度
    print('\n--- θ 标度（固定 p）---')
    lt = np.log(thetas)
    for p in ps:
        y = np.log([max(grid[(p, t)], 1e-18) for t in thetas])
        sl, _ = np.polyfit(lt, y, 1)
        print(f'  p={p:<6g}: 斜率 {sl:.3f}')
    print('\n--- p 标度（固定 θ，p∈[1e-4, 0.1]）---')
    lp = np.log([p for p in ps if p > 0])
    for th in thetas:
        y = np.log([max(grid[(p, th)], 1e-18) for p in ps if p > 0])
        sl, _ = np.polyfit(lp, y, 1)
        print(f'  θ={th:<6g}: 斜率 {sl:.3f}')

if __name__ == '__main__':
    main()
