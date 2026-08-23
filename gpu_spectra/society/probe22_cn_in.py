#!/usr/bin/env python3
"""
探针㉒：中印对照——结构同构、参数悬殊（WVS Wave 7 个体级）
================================================================
中国 CHN vs 印度 IND：满意度 Q49、幸福 Q46(1-4, 1=very happy)、
宗教重要性 Q6(1-4, 1=very important)、信任 Q57(1=trust)、
收入-幸福相关 Q288(1-10 收入等级) × Q49。
"""
import pandas as pd
import numpy as np
import json
from scipy import stats as sst

df = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv',
                 usecols=['B_COUNTRY_ALPHA', 'Q49', 'Q46', 'Q6', 'Q57', 'Q288'],
                 low_memory=False)

def clean(s, lo, hi):
    return s[(s >= lo) & (s <= hi)]

def report(tag, sub):
    print(f'\n===== {tag} =====')
    out = {}
    for v, lo, hi, nm in [('Q49', 1, 10, '满意度'), ('Q46', 1, 4, '幸福(1=very happy)'),
                          ('Q6', 1, 4, '宗教重要性(1=very imp)'),
                          ('Q57', 1, 2, '信任(1=trust)'), ('Q288', 1, 10, '收入等级')]:
        x = clean(sub[v].dropna(), lo, hi)
        out[nm] = {'n': int(len(x)), 'mean': float(x.mean()), 'std': float(x.std())}
        print(f'  {nm:18s} n={len(x):6d}  mean={x.mean():6.3f}  std={x.std():5.3f}')
    # 比例指标
    q6 = clean(sub['Q6'].dropna(), 1, 4)
    rel_imp = (q6 == 1).mean() * 100
    q57 = clean(sub['Q57'].dropna(), 1, 2)
    trust_rate = (q57 == 1).mean() * 100
    q46 = clean(sub['Q46'].dropna(), 1, 4)
    happy_rate = (q46 == 1).mean() * 100
    out['宗教非常重要比例%'] = float(rel_imp)
    out['信任比例%'] = float(trust_rate)
    out['非常幸福比例%'] = float(happy_rate)
    print(f'  宗教非常重要(1)比例 = {rel_imp:.1f}%')
    print(f'  信任(1)比例         = {trust_rate:.1f}%')
    print(f'  非常幸福(1)比例     = {happy_rate:.1f}%')
    # 收入-幸福相关 (Q288 × Q49, 均取有效)
    m = sub[['Q288', 'Q49']].dropna()
    m = m[(m['Q288'] >= 1) & (m['Q288'] <= 10) & (m['Q49'] >= 1) & (m['Q49'] <= 10)]
    if len(m) > 30:
        r, p = sst.pearsonr(m['Q288'], m['Q49'])
        out['income_sat_corr'] = {'r': float(r), 'p': float(p), 'n': int(len(m))}
        print(f'  收入×满意度 Pearson r = {r:.3f} (p={p:.2e}, n={len(m)})')
    return out

cn = df[df['B_COUNTRY_ALPHA'] == 'CHN']
ind = df[df['B_COUNTRY_ALPHA'] == 'IND']
print(f'中国样本: {len(cn)}, 印度样本: {len(ind)}')
res_cn = report('中国 CHN', cn)
res_ind = report('印度 IND', ind)

# 比值
print('\n===== 对比 =====')
print(f"满意度 std: 中 {res_cn['满意度']['std']:.3f} vs 印 {res_ind['满意度']['std']:.3f}")
print(f"宗教非常重要: 中 {res_cn['宗教非常重要比例%']:.1f}% vs 印 {res_ind['宗教非常重要比例%']:.1f}% "
      f"(印/中 = {res_ind['宗教非常重要比例%']/res_cn['宗教非常重要比例%']:.1f})")
print(f"收入×满意度 r: 中 {res_cn['income_sat_corr']['r']:.3f} vs 印 {res_ind['income_sat_corr']['r']:.3f} "
      f"(印/中 = {res_ind['income_sat_corr']['r']/res_cn['income_sat_corr']['r']:.1f})")

with open('probe22_results.json', 'w') as f:
    json.dump({'cn': res_cn, 'ind': res_ind}, f, indent=2, ensure_ascii=False)
print('\n已保存 probe22_results.json')
