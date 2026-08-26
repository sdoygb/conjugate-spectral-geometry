#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""w* 计算：2025 全矩阵（IMTS 口径 w_ij = M[i←j]+M[j←i]）
逐步收缩 CN-US 边 → 追踪 λ₂（拉普拉斯第二小特征值）崩塌 → 给出临界权重 w* 与当前距离
"""
import json
import numpy as np

PARSED = 'imts_bulk_parsed.json'

NAME2ISO = {'CN': 'CHN', 'TW': 'TWN', 'US': 'USA', 'JP': 'JPN', 'IN': 'IND', 'KR': 'KOR',
            'RU': 'RUS', 'HK': 'HKG', 'GB': 'GBR', 'CA': 'CAN', 'AU': 'AUS', 'BR': 'BRA',
            'MX': 'MEX', 'ID': 'IDN', 'SG': 'SGP', 'TH': 'THA', 'MY': 'MYS', 'VN': 'VNM',
            'PH': 'PHL', 'PK': 'PAK', 'SA': 'SAU', 'CH': 'CHE'}
ISO2NAME = {v: k for k, v in NAME2ISO.items()}
EU27 = ['AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC',
        'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK',
        'SVN', 'ESP', 'SWE']
nodes = list(NAME2ISO.keys()) + ['EU']  # 23 节点（命名沿用 24 口径）
iCN, iUS = nodes.index('CN'), nodes.index('US')

data = json.load(open(PARSED))

def import_flow(importer_iso, partner_iso, y, ind='MG_CIF_USD'):
    return data.get(importer_iso, {}).get(partner_iso, {}).get(ind, {}).get(y, 0.0)

def eu_import_from(partner_iso, y):
    return sum(import_flow(m, partner_iso, y) for m in EU27)

def edge_w(name_i, name_j, y):
    if name_i == 'EU' and name_j == 'EU':
        return 0.0
    w = 0.0
    if name_i == 'EU':
        w += eu_import_from(NAME2ISO[name_j], y)
        w += sum(import_flow(NAME2ISO[name_j], m, y) for m in EU27)
    elif name_j == 'EU':
        w += sum(import_flow(NAME2ISO[name_i], m, y) for m in EU27)
        w += eu_import_from(NAME2ISO[name_i], y)
    else:
        w += import_flow(NAME2ISO[name_i], NAME2ISO[name_j], y)
        w += import_flow(NAME2ISO[name_j], NAME2ISO[name_i], y)
    return w

def build_matrix(y):
    n = len(nodes)
    W = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            w = edge_w(nodes[i], nodes[j], y)
            W[i, j] = W[j, i] = w
    return W

def lam2_of(W):
    n = len(W)
    L = np.diag(W.sum(axis=1)) - W
    ev = np.sort(np.linalg.eigvalsh(L))
    return float(ev[1])

def br_of(W):
    n = len(W)
    ev = np.sort(np.linalg.eigvalsh(W))
    return float(sum(abs(ev[i] + ev[n - 1 - i]) for i in range(n // 2)) / (n // 2))

Y = '2025'
W0 = build_matrix(Y)
w_cnus_cur = float(W0[iCN, iUS])
lam2_0 = lam2_of(W0)
br_0 = br_of(W0)
print(f'=== 2025 基态（α=1）===')
print(f'CN-US 边权 w = {w_cnus_cur:.6e} USD = {w_cnus_cur/1e11:.4f} 百亿')
print(f'λ₂ = {lam2_0:.6e}, BR = {br_0:.6e}')
print(f'（对照 probe30_imts_2025_full: λ₂24=7.0874e10, BR24=1.7041e11）')

# ---- 扫描 α：CN-US 边 × α ----
alphas = np.linspace(1.0, 0.0, 4001)
lam2s, brs = [], []
for a in alphas:
    W = W0.copy()
    W[iCN, iUS] = W[iUS, iCN] = w_cnus_cur * a
    lam2s.append(lam2_of(W))
    brs.append(br_of(W))
lam2s = np.array(lam2s)
brs = np.array(brs)

# ---- 崩塌判据 ----
# (a) 相对阈值：λ₂ 降到初始值的 10% / 5% / 1%
lam2_ref = lam2_0
for frac, name in [(0.10, '10%'), (0.05, '5%'), (0.01, '1%')]:
    idx = np.where(lam2s <= frac * lam2_ref)[0]
    if len(idx):
        a_star = alphas[idx[0]]
        print(f'\n[阈值 {name}] λ₂ 崩塌点 α* = {a_star:.4f}  →  w* = {w_cnus_cur*a_star:.6e} ({w_cnus_cur*a_star/1e11:.4f} 百亿)')
        print(f'  当前距离: w/w* = {1/a_star:.2f}×（CN-US 边需再收缩 {(1-a_star)*100:.1f}% 才触发）')
    else:
        print(f'\n[阈值 {name}] 4001 步内未触及（λ₂ 最小 {lam2s.min():.4e} = {lam2s.min()/lam2_ref:.2%} 初始值）')

# (b) 拐点：dλ₂/dα 变化最剧烈处（有限差分二阶导峰值）
d1 = np.gradient(lam2s, alphas)
d2 = np.gradient(d1, alphas)
kink = int(np.argmax(np.abs(d2)))
print(f'\n[拐点] |d²λ₂/dα²| 峰值在 α = {alphas[kink]:.4f} → w = {w_cnus_cur*alphas[kink]:.6e} ({w_cnus_cur*alphas[kink]/1e11:.4f} 百亿)')
print(f'  该点 λ₂ = {lam2s[kink]:.4e} = {lam2s[kink]/lam2_ref:.2%} 初始值')

# (c) 谱隙闭合判定：λ₂ 与数值噪声/孤立点本征值比较——取 λ₂ 掉到 "CN-US 边贡献消失后残余连通" 的平衡值
#     扫描末段 λ₂ 的渐近值（α→0 时图仍连通，CN-US 经其他路径连通）
lam2_asym = float(lam2s[-1])
print(f'\n[渐近] α→0 时 λ₂ 残余 = {lam2_asym:.4e} = {lam2_asym/lam2_ref:.2%} 初始值')
print(f'  （含义：CN-US 边归零后，网络经 CN-TW-US / CN-JP-US / CN-EU-US 等路径仍连通的最小谱隙）')

# ---- BR 对照：崩塌时 BR 是否抬升（双高→阵营化确认）----
br_at_kink = brs[kink]
print(f'\n[BR 对照] 基态 BR={br_0:.4e}；拐点 α={alphas[kink]:.4f} 处 BR={br_at_kink:.4e}（变化 {br_at_kink/br_0-1:+.2%}）')

# ---- 保存 ----
out = {
    'year': Y, 'nodes': nodes, 'w_cnus_2025': w_cnus_cur,
    'lam2_base': lam2_0, 'br_base': br_0,
    'scan': {'alpha': alphas.tolist(), 'lam2': lam2s.tolist(), 'br': brs.tolist()},
    'thresholds': {f'{int(frac*100)}pct': {'alpha': float(alphas[np.where(lam2s <= frac*lam2_ref)[0][0]])
                                            if len(np.where(lam2s <= frac*lam2_ref)[0]) else None,
                                            'w_star': float(w_cnus_cur*alphas[np.where(lam2s <= frac*lam2_ref)[0][0]])
                                            if len(np.where(lam2s <= frac*lam2_ref)[0]) else None}
                    for frac in (0.10, 0.05, 0.01)},
    'kink': {'alpha': float(alphas[kink]), 'w': float(w_cnus_cur*alphas[kink]),
             'lam2': float(lam2s[kink]), 'br': float(br_at_kink)},
    'asymptote': {'lam2': float(lam2_asym)},
}
json.dump(out, open('wstar_cnus_2025.json', 'w'), indent=1)
print('\n已保存 wstar_cnus_2025.json')
