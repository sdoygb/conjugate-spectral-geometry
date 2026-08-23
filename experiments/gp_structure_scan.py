#!/usr/bin/env python3
"""g_p 结构比对：几何论常数族扫描 + 巧合显著性检验
规则：任何"接近"必须过显著性检验，否则视为数字命理学。
目标：g_p = 5.5856946893(16)（CODATA 2018），g_p/2 = 2.79284734463(82)
"""
import numpy as np
import itertools, math

# ---- 几何论常数清单（来源标注）----
consts = {
    'S_e':       137.035999084,   # σ* 位置处作用量值（1.5 §3.7 观测者位置）
    'sig_M':     0.777912,        # σ* 分量（1.5 §3.7）
    'sig_C':     0.210603,
    'sig_I':     0.011484,
    'Lambda_H':  150.0,           # 谱刚性带阈值（10.9 使用）
    'L':         7.0,             # κ_w+κ_w' = 4L + π/Λ_H（10.9）
    'k_eV':      3728.94,         # 电磁特征能量 eV（3.1 §5 / 3.7）
    'lam1_eff':  391.05,          # 谱间隙方向有效值（10.9）
    'lam2_eff':  59324.3,
    'kap_w':     13.092026,       # H^W 前置因子（10.9）
    'kap_wp':    14.928918,
    'Phi_11':    12.4415,         # 渗透函数（10.9）
    'Phi_12':    22.6281,
    'R_me':      1833.8,          # 三夸克等效 m_p/m_e（10.9 框架内构造）
    'a_HW':      1.577,           # H^W 矩阵元（10.9）
    'b_HW':      0.867,
    'sinIp':     0.881,           # 质子构型（3.7 §4.2.5）
    'sinCp':     0.471,
    'sinIe':     0.102960840,     # 电子基态（3.7）
    'four_pi':   4.0/math.pi,
    'pi':        math.pi,
    'p2':        2.0, 'p3': 3.0, 'p5': 5.0,   # 互锁 {2,3,5}
}
names = list(consts.keys())
vals  = np.array([consts[n] for n in names])

# ---- 目标值 ----
gp   = 5.5856946893
gp2  = gp/2.0
targets = {'g_p': gp, 'g_p/2': gp2, 'g_p-4': gp-4.0, '1/g_p': 1.0/gp, 'g_p/4': gp/4.0}

# ---- 表达式族：两两运算 + 一元 + 简单三元 ----
def gen_exprs(vals, names):
    """返回 (表达式描述, 数值) 列表"""
    out = []
    n = len(vals)
    for i in range(n):
        a, na = vals[i], names[i]
        out.append((na, a))
        out.append(('1/'+na, 1.0/a))
        out.append(('sqrt('+na+')', math.sqrt(a)))
        out.append(('sq('+na+')', a*a))
        out.append((na+'+1', a+1.0))
        out.append((na+'-1', a-1.0))
        out.append((na+'/2', a/2.0))
        out.append(('2*'+na, 2.0*a))
        for j in range(i+1, n):
            b, nb = vals[j], names[j]
            out.append(('(%s+%s)'%(na,nb), a+b))
            out.append(('(%s-%s)'%(na,nb), a-b))
            out.append(('(%s*%s)'%(na,nb), a*b))
            if abs(b) > 1e-12: out.append(('(%s/%s)'%(na,nb), a/b))
            if abs(a) > 1e-12: out.append(('(%s/%s)'%(nb,na), b/a))
            out.append(('sqrt(%s*%s)'%(na,nb), math.sqrt(abs(a*b))))
            out.append(('(%s+%s)/2'%(na,nb), (a+b)/2.0))
            out.append(('(%s+%s)/%s'%(na,nb,'pi'), (a+b)/math.pi))
            out.append(('(%s-%s)/%s'%(na,nb,'pi'), (a-b)/math.pi))
            out.append(('(%s*%s)/%s'%(na,nb,'pi'), a*b/math.pi))
            out.append(('(%s+%s)/%s'%(na,nb,'S_e'), (a+b)/137.035999084))
    return out

def scan(target, exprs, tol=1e-5):
    hits = []
    for desc, v in exprs:
        if v <= 0: continue
        rel = abs(v - target)/target
        if rel < tol:
            hits.append((rel, desc, v))
    hits.sort()
    return hits

exprs = gen_exprs(vals, names)
print(f"常数数: {len(vals)}, 表达式数: {len(exprs)}, 目标数: {len(targets)}")
print("="*70)
for tname, tval in targets.items():
    hits = scan(tval, exprs, tol=1e-4)
    print(f"\n目标 {tname} = {tval:.10f}")
    print(f"  相对偏差 < 1e-4 的命中数: {len(hits)}")
    for rel, desc, v in hits[:10]:
        flag = " ***" if rel < 1e-6 else ""
        print(f"    {rel:.2e}  {desc} = {v:.10f}{flag}")

# ---- 显著性检验：随机对照 ----
rng = np.random.default_rng(42)
N_trial = 200
def random_consts(rng, k=len(vals)):
    # 与真实常数同数量级分布的随机数：混合 [0.01,1], [1,10], [10,1000], [1000,10^5]
    n1, n2, n3, n4 = 8, 8, 6, 3
    c = np.concatenate([
        rng.uniform(0.005, 1.0, n1),
        rng.uniform(1.0, 10.0, n2),
        rng.uniform(10.0, 1000.0, n3),
        rng.uniform(1000.0, 1e5, n4)])
    return c

# 真实集的强命中数（< 1e-5）
real_hits = {t: len(scan(tv, exprs, tol=1e-5)) for t, tv in targets.items()}
print("\n" + "="*70)
print("显著性检验：真实常数集 vs 随机常数集（相对偏差 < 1e-5 的命中数）")
print(f"真实集: {real_hits}")
rand_hits = {t: [] for t in targets}
for trial in range(N_trial):
    rc = random_consts(rng)
    rexprs = gen_exprs(rc, [f'x{i}' for i in range(len(rc))])
    for t, tv in targets.items():
        rand_hits[t].append(len(scan(tv, rexprs, tol=1e-5)))
for t in targets:
    arr = np.array(rand_hits[t])
    mean, std = arr.mean(), arr.std()
    z = (real_hits[t] - mean)/std if std > 0 else float('inf')
    print(f"  {t}: 真实={real_hits[t]}, 随机均值={mean:.1f}±{std:.1f}, z={z:.1f}")

# ---- √7.8 候选（简单数学表达式族，非几何常数）----
print("\n" + "="*70)
print("√(a/b) 族对 g_p/2 的邻居密度检验（a,b ≤ 2000）")
target = gp2
best = []
for b in range(1, 2001):
    lo = int((target-5e-6)**2 * b) - 1
    hi = int((target+5e-6)**2 * b) + 1
    for a in range(max(1, lo), hi+1):
        v = math.sqrt(a/b)
        rel = abs(v - target)/target
        if rel < 2e-5:
            best.append((rel, a, b, v))
best.sort()
for rel, a, b, v in best[:8]:
    print(f"  rel={rel:.2e}  sqrt({a}/{b}) = {v:.10f}")
# 区间 [2.79, 2.80] 内 √(a/b) 的总密度
cnt = 0
for b in range(1, 2001):
    lo = int(2.79**2 * b); hi = int(2.80**2 * b)
    cnt += max(0, hi - lo)
print(f"√(a/b), a,b≤2000 在 [2.79,2.80] 内的个数: {cnt} → 平均间距 ≈ {(2.80-2.79)/max(cnt,1):.2e}")
print(f"g_p/2 与 √(39/5)=√7.8 的相对偏差: {abs(math.sqrt(7.8)-target)/target:.2e}")
print(f"g_p/2 与 √7.8 的接近度在该密度下的显著性: ~{(2.80-2.79)/max(cnt,1)/abs(math.sqrt(7.8)-target):.0f} 倍于平均间距")
