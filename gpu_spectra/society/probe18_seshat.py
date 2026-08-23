#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑱：Seshat 真实数据检验"前5世纪尼泊尔地区上圆满者"假说
数据：Seshat Global History Databank (github.com/datasets/seshat)
  - axial_dataset.05.2018.csv  (轴心时代 10 地区道德指标)
  - mr_dataset.04.2021.csv     (道德化宗教数据集，34 政体)
分析：Middle Ganga(恒河中游) = 佛陀核心区直接代理
      检验：破缺(十六大国)→认知层操作(佛陀时代)→制度层补缺(孔雀王朝)链条
"""
import csv, json
from collections import defaultdict

results = {}

# ============ 1. Axial 数据集：轴心窗口 (前800~前200) 各地区轨迹 ============
axial = defaultdict(list)
with open('seshat_tmp/axial_dataset.05.2018.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        d = int(row['Date.From'])
        if -800 <= d <= -200:
            try:
                axial[row['NGA']].append((d, float(row['sum'])))
            except ValueError:
                pass

axial_traj = {p: sorted(v) for p, v in axial.items()}
results['axial_window_trajectory'] = {
    p: [(d, s) for d, s in sorted(v)] for p, v in axial.items()
}

print("=== Axial 窗口 (前800~前200) 各地区 sum 轨迹 ===")
for p in sorted(axial_traj):
    pts = axial_traj[p]
    vals = [s for _, s in pts]
    start = vals[0]
    maxv = max(vals)
    jump = maxv - start
    print(f"{p:35s} start={start} max={maxv} jump={jump}  轨迹={vals}")
results['axial_jumps'] = {
    p: {'start': vals[0], 'max': max(vals), 'jump': max(vals) - vals[0],
        'traj': vals} for p, vals in
    ((p, [s for _, s in sorted(v)]) for p, v in axial.items())
}

# ============ 2. mr_dataset：Middle Ganga 时间线 ============
mr = defaultdict(list)
with open('seshat_tmp/mr_dataset.04.2021.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        mr[row['NGA']].append((int(row['Start']), int(row['End']),
                               row['MSP_sum'], row['commoners'],
                               row['afterlife'], row['primary']))

def show(p):
    pts = sorted(mr[p], key=lambda x: x[0])
    print(f"\n=== {p} ===")
    for s, e, m, com, aft, pr in pts:
        print(f"  {s} ~ {e}: MSP={m} 平民={com} 来世={aft} 主导={pr}")
    return pts

mg = show('Middle Ganga')
results['middle_ganga_timeline'] = [
    {'start': s, 'end': e, 'MSP': m, 'commoners': com, 'afterlife': aft, 'primary': pr}
    for s, e, m, com, aft, pr in mg
]

# 三窗口对照（全地区）
print("\n=== 三窗口对照（前1500~前601 / 前600~前325 / 前324~前1） ===")
targets = ['Middle Ganga', 'Kachi Plain', 'Middle Yellow River Valley',
           'Susiana', 'Kansai', 'Latium', 'Crete', 'Galilee',
           'Konya Plain', 'Upper Egypt']
comp = {}
for p in targets:
    pts = sorted(mr[p], key=lambda x: x[0])
    w = {}
    for s, e, m, com, aft, pr in pts:
        if -1500 <= s and e <= -601:
            w['w1'] = {'MSP': m, '平民': com}
        if -600 <= s and e <= -325:
            w['w2'] = {'MSP': m, '平民': com}
        if -324 <= s and e <= -1:
            w['w3'] = {'MSP': m, '平民': com}
    comp[p] = w
    def fmt(x):
        return f"{x['MSP']}(平民{x['平民']})" if x else "—"
    print(f"{p:35s} w1={fmt(w.get('w1')):12s} w2={fmt(w.get('w2')):12s} w3={fmt(w.get('w3'))}")
results['three_window_comparison'] = comp

# ============ 3. 关键发现总结 ============
print("\n=== 关键发现 ===")
print("""
1. Middle Ganga(恒河中游, 佛陀核心区) 1500年首次变化恰在佛陀时代窗口(前600~前325)：
   平民道德 0.5→1.0（commoners 纳入道德体系），MSP 4→4.5
2. 满分跃升(4.5→7, primary=1)发生在窗口3(前324~前1)——佛陀后约200-300年，
   对应孔雀王朝/阿育王的制度层补缺
3. 对照地区：黄河(孔子时代)窗口2无数据；Susiana 5→6 渐进；罗马 4→4.5 小变；
   埃及全程7(早已道德化)；Kachi Plain 窗口3=7(孔雀王朝覆盖印度河)
4. 唯一在佛陀时代窗口出现"平民道德纳入"跃升的地区 = Middle Ganga
""")

with open('probe18_results.json', 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print("已保存 probe18_results.json")
