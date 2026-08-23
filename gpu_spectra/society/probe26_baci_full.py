#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑩'/㉓'/㉔'：BACI 真实双边贸易流升级
============================================
把探针㉓(6节点谱分析)与探针㉔(补缺传播序列)的估算边权替换为 BACI 2024 真实值，
并补上探针⑩ 遗留的贸易通道 Mantel 检验（66 国真实双边矩阵）。

数据:
  baci_6node_yearly.csv  : 1995-2024 逐年 6 节点有向贸易（亿美元）
  baci_66_y2023.csv      : 66 国 2023 双边贸易（千美元）
  country_codes          : ISO 数字码 -> ISO3
  dist_cepii.xls         : 地理距离（偏 Mantel 控制）
"""
import pandas as pd
import numpy as np
import json, os
from scipy import stats

SOCIETY = os.path.dirname(os.path.abspath(__file__))
DL = '/Users/oygb/Downloads'

# ---------- 1. 6节点 2024 真实双向边权（亿美元） ----------
y = pd.read_csv(f'{SOCIETY}/baci_6node_yearly.csv')
row = y[y.year == 2024].iloc[0]
pairs = [
    ('CN', 'TW'), ('CN', 'JP'), ('CN', 'IN'), ('CN', 'US'), ('CN', 'EU'),
    ('TW', 'JP'), ('TW', 'IN'), ('TW', 'US'), ('TW', 'EU'),
    ('JP', 'IN'), ('JP', 'US'), ('JP', 'EU'),
    ('IN', 'US'), ('IN', 'EU'), ('US', 'EU'),
]
W = {}
for a, b in pairs:
    W[(a, b)] = row[f'{a}->{b}'] + row[f'{b}->{a}']   # 双向合计，亿美元

names = ['CN', 'TW', 'JP', 'IN', 'US', 'EU']
idx = {n: i for i, n in enumerate(names)}
base = max(W.values())   # 以最大边归一化（US-EU）

def _wk(a, b):
    return (a, b) if (a, b) in W else (b, a)

def to_mat(scale=None):
    M = np.zeros((6, 6))
    for (a, b), v in W.items():
        M[idx[a], idx[b]] = M[idx[b], idx[a]] = v / base
    if scale:
        for (a, b), s in scale.items():
            k = _wk(a, b)
            M[idx[a], idx[b]] = M[idx[b], idx[a]] = W[k] * s / base
    return M

def laplacian_lambda2(M):
    L = np.diag(M.sum(axis=1)) - M
    return float(np.sort(np.linalg.eigvalsh(L))[1])

def bipartite_residual(M):
    ev = np.sort(np.linalg.eigvalsh(M))
    n = len(ev)
    return float(sum(abs(ev[i] + ev[n-1-i]) for i in range(n//2)) / (n//2))

def tw_share(M):
    total = sum(M[idx[a], idx['TW']] for a in ['CN', 'US', 'EU', 'JP'])
    return {a: float(M[idx[a], idx['TW']] / total) for a in ['CN', 'US', 'EU', 'JP']}

def report(tag, M):
    l2, br = laplacian_lambda2(M), bipartite_residual(M)
    print(f"{tag:30s} λ₂={l2:.4f}   BR={br:.4f}")
    return l2, br

print("=== A. 6节点真实边权（2024 双向合计，亿美元）===")
for (a, b), v in W.items():
    print(f"  {a}-{b}: {v:9.2f}")
print(f"  基准(最大边 US-EU) = {base:.2f} 亿美元")

W0 = to_mat()
res = {'A_edges': {f'{a}-{b}': v for (a, b), v in W.items()}, 'base': base}

# ---------- 2. 情景矩阵 S0-S8（真实边权） ----------
print("\n=== B. 情景矩阵（真实边权）===")
S = {}
S['S0'] = W0.copy(); report('S0 现状(2024真实)', S['S0'])
S['S1'] = to_mat({('CN', 'US'): 0.3}); report('S1 中美脱钩 CN-US×0.3', S['S1'])
S['S2'] = to_mat({('US', 'TW'): 1.5}); report('S2 美台强化 US-TW×1.5', S['S2'])
S['S3'] = to_mat({('EU', 'IN'): 2.0}); report('S3 欧印强化 EU-IN×2', S['S3'])
S['S4'] = to_mat({('CN', 'US'): 0.3, ('US', 'TW'): 1.5, ('EU', 'IN'): 2.0}); report('S4 组合(脱钩+美台+欧印)', S['S4'])
S['S5'] = to_mat({('CN', 'TW'): 0.5}); report('S5 两岸削弱 CN-TW×0.5', S['S5'])
S['S6'] = to_mat({('CN', 'TW'): 0.5, ('US', 'TW'): 1.5}); report('S6 危机组合(两岸弱+美台强)', S['S6'])
S['S7'] = to_mat({('CN', 'US'): 0.3, ('CN', 'TW'): 0.5, ('US', 'TW'): 1.5, ('EU', 'IN'): 2.0}); report('S7 全组合', S['S7'])
# S8 完全二部极限: {CN,TW,JP} vs {IN,US,EU}，组间=真实平均边权，组内=0
M8 = np.zeros((6, 6))
grpA, grpB = ['CN', 'TW', 'JP'], ['IN', 'US', 'EU']
avg = np.mean([W[(a, b)] for a in grpA for b in grpB]) / base
for a in grpA:
    for b in grpB:
        M8[idx[a], idx[b]] = M8[idx[b], idx[a]] = avg
S['S8'] = M8; report('S8 完全二部极限(理论)', S['S8'])

res['B_scenarios'] = {k: {'lambda2': laplacian_lambda2(v), 'bipartite': bipartite_residual(v)} for k, v in S.items()}

# ---------- 3. r 扫描：US-TW / CN-TW 强度比 ----------
print("\n=== C. r 扫描（US-TW / CN-TW 强度比，二部化相变）===")
base_cntw = W[('CN', 'TW')]
scan = []
for r in np.linspace(0.1, 3.0, 30):
    M = to_mat({('US', 'TW'): r * base_cntw / W[_wk('US', 'TW')]})
    scan.append({'r': float(r), 'lambda2': laplacian_lambda2(M), 'bipartite': bipartite_residual(M)})
for r0 in [0.5, 1.0, 1.5, 2.0, 2.5]:
    s = next(s for s in scan if abs(s['r'] - r0) < 0.01)
    print(f"  r={r0:.1f}: λ₂={s['lambda2']:.4f}  BR={s['bipartite']:.4f}")
res['C_scan'] = scan
# 真实 r
r_real = W[_wk('US', 'TW')] / base_cntw
print(f"  真实 r(2024) = US-TW/CN-TW = {W[_wk('US','TW')]:.1f}/{base_cntw:.1f} = {r_real:.3f}")
res['C_r_real'] = r_real

# ---------- 4. TW 份额 ----------
print("\n=== D. 台湾耦合份额（CN/US/EU/JP）===")
for tag in ['S0', 'S2', 'S4', 'S6']:
    sh = tw_share(S[tag])
    print(f"  {tag}: CN={sh['CN']*100:5.1f}%  US={sh['US']*100:5.1f}%  EU={sh['EU']*100:5.1f}%  JP={sh['JP']*100:5.1f}%")
res['D_tw_share'] = {k: tw_share(S[k]) for k in ['S0', 'S2', 'S4', 'S6']}

# ---------- 5. 传播序列 P1/P2/P3（真实边权） ----------
print("\n=== E. 补缺传播序列（真实边权）===")
P1 = to_mat({('CN', 'US'): 0.3, ('US', 'TW'): 1.5, ('EU', 'IN'): 2.0,
              ('CN', 'TW'): 1.3, ('CN', 'JP'): 1.2, ('CN', 'IN'): 1.3})
report('P1 东方补缺(基于S4)', P1)
P2 = to_mat({('CN', 'US'): 0.8, ('US', 'TW'): 1.5, ('EU', 'IN'): 2.0,
             ('CN', 'TW'): 1.3, ('CN', 'JP'): 1.2, ('CN', 'IN'): 1.3, ('CN', 'EU'): 1.2})
report('P2 西方桥恢复(基于P1)', P2)
P3 = W0.copy()
report('P3 回S0', P3)
l2_s4 = laplacian_lambda2(S['S4'])
d1 = laplacian_lambda2(P1) - l2_s4
d2 = laplacian_lambda2(P2) - laplacian_lambda2(P1)
print(f"\n  Δ₁ 东方补缺 = {d1:.4f} ({d1/(d1+d2)*100:.1f}%)")
print(f"  Δ₂ 西方桥   = {d2:.4f} ({d2/(d1+d2)*100:.1f}%)")
print(f"  比值 Δ₁/Δ₂  = {d1/d2:.2f}")
print(f"  P2 vs S0: {laplacian_lambda2(P2):.4f} vs {laplacian_lambda2(W0):.4f} ({(laplacian_lambda2(P2)-laplacian_lambda2(W0))/laplacian_lambda2(W0)*100:+.1f}%)")
res['E_sequence'] = {
    'S4': laplacian_lambda2(S['S4']), 'P1': laplacian_lambda2(P1), 'P2': laplacian_lambda2(P2), 'P3': laplacian_lambda2(P3),
    'd1': d1, 'd2': d2, 'ratio': d1/d2, 'tw_share': {k: tw_share(v) for k, v in [('S4', S['S4']), ('P1', P1), ('P2', P2)]}}

# ---------- 6. 6节点逐年 λ₂/BR 轨迹（1995-2024） ----------
print("\n=== F. 6节点逐年耦合谱轨迹（1995-2024）===")
traj = []
for _, r_ in y.iterrows():
    M = np.zeros((6, 6))
    for a, b in pairs:
        v = r_[f'{a}->{b}'] + r_[f'{b}->{a}']
        M[idx[a], idx[b]] = M[idx[b], idx[a]] = v / base
    traj.append({'year': int(r_.year), 'lambda2': laplacian_lambda2(M), 'bipartite': bipartite_residual(M)})
for t in traj[::5] + traj[-1:]:
    print(f"  {t['year']}: λ₂={t['lambda2']:.4f}  BR={t['bipartite']:.4f}")
res['F_trajectory'] = traj

# ---------- 7. 66国贸易通道 Mantel（探针⑩'） ----------
print("\n=== G. 66国贸易耦合 Mantel（2023 双边矩阵）===")
df66 = pd.read_csv(f'{SOCIETY}/baci_66_y2023.csv')   # i,j,v 千美元
cc = pd.read_csv(f'{DL}/BACI_HS22_V202601/country_codes_V202601.csv')
code2iso = dict(zip(cc.country_code, cc.country_iso3))

# 66 国 ISO3 清单（来自 WVS）
wvs = pd.read_csv(f'{SOCIETY}/WVS_Cross-National_Wave_7_csv_v6_0.csv',
                  usecols=['B_COUNTRY_ALPHA', 'Q50'])
wvs = wvs[wvs.Q50 >= 1]
sat = wvs.groupby('B_COUNTRY_ALPHA').Q50.mean()
iso66 = sorted(sat.index)
print(f"  WVS 66国满意度均值就绪（{len(iso66)}国）")

# 66国贸易矩阵（对称化 + log1p）
T = np.zeros((len(iso66), len(iso66)))
iso2i = {iso: i for i, iso in enumerate(iso66)}
matched = 0
for _, rr in df66.iterrows():
    a, b = code2iso.get(rr.i), code2iso.get(rr.j)
    if a in iso2i and b in iso2i:
        T[iso2i[a], iso2i[b]] += rr.v
        T[iso2i[b], iso2i[a]] += rr.v
        matched += 1
print(f"  BACI→66国匹配边数: {matched}")
Tlog = np.log1p(T / 1000.0)   # 千美元→百万美元后 log1p

# |Δsat| 矩阵
satv = np.array([sat[i] for i in iso66])
Dsat = np.abs(satv[:, None] - satv[None, :])

def mantel(X, Y, nperm=2000, seed=42):
    iu = np.triu_indices(len(X), 1)
    x, y = X[iu], Y[iu]
    rho = stats.spearmanr(x, y).statistic
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(nperm):
        yp = rng.permutation(y)
        cnt += (abs(stats.spearmanr(x, yp).statistic) >= abs(rho))
    return rho, (cnt + 1) / (nperm + 1)

rho_t, p_t = mantel(Tlog, Dsat)
print(f"  Mantel ρ(贸易强度 × |Δsat|) = {rho_t:.4f}  p={p_t:.4f}")
res['G_trade_mantel'] = {'rho': rho_t, 'p': p_t, 'matched_edges': matched}

# 与地理距离的偏 Mantel（控制地理后贸易是否仍有耦合信息）
try:
    geo = pd.read_excel(f'{SOCIETY}/dist_cepii.xls')
    gmat = np.zeros((len(iso66), len(iso66)))
    g_iso = {}
    for _, rr in geo.iterrows():
        g_iso[rr.iso_o] = rr.iso_d  # 简化: 记录出现的 ISO
    # 用 dist 表构建 66×66
    geo_pairs = {}
    for _, rr in geo.iterrows():
        a, b = rr.iso_o, rr.iso_d
        if a in iso2i and b in iso2i:
            try:
                d = float(rr.distw)
            except (ValueError, TypeError):
                continue
            geo_pairs[(iso2i[a], iso2i[b])] = geo_pairs.get((iso2i[a], iso2i[b]), 0.0) + d
    for (a, b), d in geo_pairs.items():
        gmat[a, b] = gmat[b, a] = d
    iu = np.triu_indices(len(iso66), 1)
    gv = gmat[iu]
    tv, dv = Tlog[iu], Dsat[iu]
    ok = gv > 0
    # 残差化: X ~ g, Y ~ g
    def resid(v, g):
        g1 = np.column_stack([np.ones_like(g), g])
        beta, *_ = np.linalg.lstsq(g1, v, rcond=None)
        return v - g1 @ beta
    rt = resid(tv[ok], gv[ok])
    rd = resid(dv[ok], gv[ok])
    rho_partial = stats.spearmanr(rt, rd).statistic
    rng2 = np.random.default_rng(123)
    cntp = 0
    for _ in range(2000):
        rdp = rng2.permutation(rd)
        cntp += (abs(stats.spearmanr(rt, rdp).statistic) >= abs(rho_partial))
    p_partial = (cntp + 1) / 2001
    print(f"  偏 Mantel（控制地理距离）: ρ={rho_partial:.4f}  p={p_partial:.4f}")
    res['G_trade_partial_geo'] = {'rho': rho_partial, 'p': p_partial, 'n': int(ok.sum())}
except Exception as e:
    print(f"  地理偏 Mantel 失败: {e}")

# ---------- 8. 66国全耦合图 λ₂/BR（2023） ----------
print("\n=== H. 66国全耦合图（2023 贸易）===")
deg = T.sum(axis=1)
mask = deg > 0
Tm = T[np.ix_(mask, mask)]
Tn = Tm / Tm.max()
L = np.diag(Tn.sum(axis=1)) - Tn
ev = np.sort(np.linalg.eigvalsh(L))
l2_66 = float(ev[1])
evA = np.sort(np.linalg.eigvalsh(Tn))
br_66 = float(sum(abs(evA[i] + evA[len(evA)-1-i]) for i in range(len(evA)//2)) / (len(evA)//2))
print(f"  66国全图（{int(mask.sum())} 国非零度）: λ₂={l2_66:.6f}  BR={br_66:.6f}")
res['H_66graph'] = {'n_active': int(mask.sum()), 'lambda2': l2_66, 'bipartite': br_66}

with open(f'{SOCIETY}/probe26_results.json', 'w') as f:
    json.dump(res, f, indent=2, ensure_ascii=False, default=float)
print("\n已保存 probe26_results.json")
