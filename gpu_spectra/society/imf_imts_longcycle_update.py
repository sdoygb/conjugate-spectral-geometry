#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针㉕ csv 更新：imf_dots_longcycle.csv 1948-2023 → 1948-2025
用 IMTS API 数据重建 14 节点口径（与 probe31_longcycle.py 完全一致）：
  A[i,j] = max(i 报告 XG 到 j, j 报告 MG 从 i) → 对称化 → ÷最大边 → λ₂ + BR
TW 无报告：TW 边由伙伴报告补全（max(X_i→TW, 0)）
"""
import json
import numpy as np
import csv

data = json.load(open('imts_bulk_parsed.json'))

REPORT = {'US':'USA','GB':'GBR','FR':'FRA','DE':'DEU','IT':'ITA','JP':'JPN','IN':'IND',
          'CN':'CHN','CA':'CAN','AU':'AUS','KR':'KOR','RU':'RUS'}
NODES = list(REPORT.keys()) + ['TW']
ISO2NODE = {v: k for k, v in REPORT.items()}
NODE2ISO = {'TW': 'TWN'}

def build_matrix(year):
    A = np.zeros((len(NODES), len(NODES)))
    idx = {k: i for i, k in enumerate(NODES)}
    # 每条有向边 i→j：max(X_i→j, M_j←i)
    for i in NODES:
        for j in NODES:
            if i == j:
                continue
            ri = REPORT.get(i)  # i 的报告 ISO3（TW=None）
            rj = REPORT.get(j)
            v = 0.0
            if ri:  # i 报告出口到 j
                v = max(v, data.get(ri, {}).get(NODE2ISO.get(j, REPORT.get(j, '')), {})
                        .get('XG_FOB_USD', {}).get(year, 0.0))
            if rj:  # j 报告从 i 进口
                v = max(v, data.get(rj, {}).get(NODE2ISO.get(i, REPORT.get(i, '')), {})
                        .get('MG_CIF_USD', {}).get(year, 0.0))
            A[idx[i], idx[j]] = v
    Asym = np.maximum(A, A.T)
    return Asym, idx

def lambda2(M):
    L = np.diag(M.sum(axis=1)) - M
    ev = np.sort(np.linalg.eigvalsh(L))
    return float(ev[1]) if len(ev) > 1 else float('nan')

def br(M):
    ev = np.sort(np.linalg.eigvalsh(M))
    n = len(ev)
    return float(sum(abs(ev[i] + ev[n - 1 - i]) for i in range(n // 2)) / (n // 2))

years = ['2022', '2023', '2024', '2025']
new_rows = []
print('=== 14 节点 IMTS 重建（2022-2025）===')
for yr in years:
    A, idx = build_matrix(yr)
    deg = A.sum(axis=1)
    active = [k for k in NODES if deg[idx[k]] > 0]
    sub_idx = [idx[k] for k in active]
    M = A[np.ix_(sub_idx, sub_idx)]
    maxw = float(M.max())
    Mn = M / maxw if maxw > 0 else M
    l2, b = lambda2(Mn), br(Mn)
    row = {'year': int(yr), 'n_active': len(active), 'lambda2': l2, 'BR': b,
           'active': ','.join(active), 'total_usd': float(A.sum()), 'max_edge_usd': maxw}
    new_rows.append(row)
    print(f'{yr}: n={len(active)} λ₂={l2:.4f} BR={b:.4f} 最大边={maxw/1e9:.1f}B$ 活跃={active}')

# 关键边归一化权重
print('\n=== 关键边（归一化，最大边=1）===')
for yr in years:
    A, idx = build_matrix(yr)
    deg = A.sum(axis=1)
    active = [k for k in NODES if deg[idx[k]] > 0]
    sub_idx = [idx[k] for k in active]
    M = A[np.ix_(sub_idx, sub_idx)]
    Mn = M / M.max() if M.max() > 0 else M
    def w(a, b):
        if a not in active or b not in active:
            return float('nan')
        return Mn[active.index(a), active.index(b)]
    print(f'{yr}: CN-US={w("CN","US"):.3f} CN-JP={w("CN","JP"):.3f} CN-TW={w("CN","TW"):.3f} '
          f'CN-IN={w("CN","IN"):.3f} US-DE={w("US","DE"):.3f} TW-US={w("TW","US"):.3f}')

# 重叠验证 2022/2023 vs csv
old = list(csv.DictReader(open('imf_dots_longcycle.csv')))
print('\n=== 重叠验证（csv 2022/2023 vs IMTS 重建）===')
for r in new_rows[:2]:
    o = next(x for x in old if int(x['year']) == r['year'])
    print(f'{r["year"]}: λ₂ csv={float(o["lambda2"]):.4f} new={r["lambda2"]:.4f} | '
          f'BR csv={float(o["BR"]):.4f} new={r["BR"]:.4f} | max csv={float(o["max_edge_usd"])/1e9:.1f}B new={r["max_edge_usd"]/1e9:.1f}B')

# 拼接写入
final = old + [{'year': str(r['year']), 'n_active': str(r['n_active']),
                'lambda2': repr(r['lambda2']), 'BR': repr(r['BR']),
                'active': r['active'], 'total_usd': repr(r['total_usd']),
                'max_edge_usd': repr(r['max_edge_usd'])} for r in new_rows[2:]]
with open('imf_dots_longcycle.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=old[0].keys())
    w.writeheader()
    w.writerows(final)
print(f'\n已更新 imf_dots_longcycle.csv: {final[0]["year"]}-{final[-1]["year"]} 共 {len(final)} 行')

print('\n=== 2024-2025 新增行 ===')
for r in final[-2:]:
    print(r)
