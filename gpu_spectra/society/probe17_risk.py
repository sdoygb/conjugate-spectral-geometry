#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑰：国家冲突风险排名 —— "谁更容易打"
================================================
几何论映射：
  和平态 = 纤维化锁定态；战争 = 破缺事件（无记忆泊松，探针⑯）
  因此"谁更容易打"的预测 = 估计每个国家的破缺率 λ_b（历史经验）
  + 结构判别修正（纤维化完整度代理：满意度国内离散度 std、GDP、制度质量）
设计（透明评分，不装黑箱）：
  risk = λ_b_hist（历史破缺频率，主项）
       + 当前状态项（2023-2025 冲突中 → +；刚结束 <3年 → 微弱 + 重构粘性）
       + 结构修正（弱权重，因探针⑯ p=0.176 不显著，诚实标注）
输出三层：
  Tier A: 当前冲突中（最可能继续/复发）
  Tier B: 历史高 λ_b + 当前和平（最可能新爆发）
  Tier C: 无冲突史但结构脆弱（潜在首爆，标注为外推）
数据：UCDP v26.1 (1946-2025) + WVS7 满意度 + WB GDP + QoG WGI
"""
import csv, json
from collections import defaultdict
from statistics import mean, pstdev
import numpy as np

# ---------- 1. UCDP 冲突状态序列（UCDP location 名 → ISO3） ----------
rev = json.load(open('ucdp2iso.json'))
years = np.arange(1946, 2026)

conf_cy = defaultdict(set)   # iso -> set(years in conflict)
with open('UcdpPrioConflict_v26_1.csv', newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        locs = [x.strip() for x in str(row.get('location', '')).split(',') if x.strip()]
        yr = int(row['year'])
        for loc in locs:
            iso = rev.get(loc)
            if iso:
                conf_cy[iso].add(yr)

# ---------- 2. 每国：λ_b、冲突年数、最近状态 ----------
def segments_of(seq):
    """连续相同状态段长列表"""
    segs = []
    cur, clen = seq[0], 1
    for s in seq[1:]:
        if s == cur:
            clen += 1
        else:
            segs.append((cur, clen))
            cur, clen = s, 1
    segs.append((cur, clen))
    return segs

rows = []
for iso, cys in conf_cy.items():
    seq = np.array([1 if y in cys else 0 for y in years])
    segs = segments_of(seq)
    peace_lens = [l for s, l in segs if s == 0]
    war_lens = [l for s, l in segs if s == 1]
    lam_b = 1.0 / mean(peace_lens) if peace_lens else 0.0
    in_conf_2025 = seq[-1] == 1
    # 最近和平段长度（若当前和平）
    last_peace = peace_lens[-1] if peace_lens and not in_conf_2025 else None
    # 最近冲突结束年（若当前和平）
    last_war_end = None
    if not in_conf_2025 and war_lens:
        # 找最后一个 1 段的结束年
        pos = 0
        for s, l in segs:
            pos += l
            if s == 1:
                last_war_end = years[pos - 1]
    rows.append(dict(iso=iso, lam_b=lam_b, n_war_years=int(cys.__len__()),
                     in_conf_2025=in_conf_2025, last_peace=last_peace,
                     last_war_end=last_war_end, war_lens_mean=mean(war_lens) if war_lens else None))
df = pd.DataFrame(rows) if False else rows

# ---------- 3. 结构变量：WVS 满意度 std ----------
sat_std, sat_mean = {}, {}
with open('WVS_Cross-National_Wave_7_csv_v6_0.csv', newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    by_c = defaultdict(list)
    for row in r:
        try:
            q = int(row['Q50'])
        except (ValueError, KeyError, TypeError):
            continue
        if 1 <= q <= 10:
            by_c[row['B_COUNTRY_ALPHA']].append(q)
for a, vals in by_c.items():
    if len(vals) >= 30:
        sat_std[a] = pstdev(vals)
        sat_mean[a] = mean(vals)

# ---------- 4. GDP（世界银行, 最近有效年） ----------
gdp = {}
with open('wb_gdp.json', encoding='utf-8') as f:
    wb = json.load(f)
    for entry in wb:
        try:
            iso = entry['countryiso3code']
            yr = int(entry['date'])
            val = entry['value']
        except (KeyError, TypeError, ValueError):
            continue
        if val is not None and (iso not in gdp or yr > gdp[iso][0]):
            gdp[iso] = (yr, float(val))

# ---------- 5. WGI（QoG: wgi_pv / wgi_rq / wgi_ge 等, 2022 最新） ----------
wgi = {}
import re
with open('qog_std_ts_jan25.csv', newline='', encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter=';')
    # QoG 用 ccodealp (ISO3) + year
    for row in r:
        try:
            yr = int(row.get('year', 0))
            if yr < 2020:
                continue
            iso = row.get('ccodealp', '')
            wgi_cols = [k for k in row.keys() if k.startswith('wgi_')]
            vals = [float(row[k]) for k in wgi_cols if row.get(k) not in ('', None)]
            if iso and vals and (iso not in wgi or yr > wgi[iso][0]):
                wgi[iso] = (yr, float(np.mean(vals)))
        except (ValueError, KeyError, TypeError):
            continue

# ---------- 6. 评分 ----------
# 主项：λ_b（历史破缺率）
# 当前状态项：冲突中 +0.15；刚结束(<3年) +0.05（重构粘性, 探针⑯ 微弱自持）
# 结构修正（弱权重, 诚实标注 p=0.176 不显著）：
#   sat_std z×0.10（破缺判别方向）、logGDP z×(-0.08)（文献共识弱信号）、WGI z×(-0.08)

all_std = [sat_std[r['iso']] for r in df if r['iso'] in sat_std]
all_gdp = [np.log(gdp[r['iso']][1]) for r in df if r['iso'] in gdp]
all_wgi = [wgi[r['iso']][1] for r in df if r['iso'] in wgi]
mu_s, sd_s = np.mean(all_std), np.std(all_std)
mu_g, sd_g = np.mean(all_gdp), np.std(all_gdp)
mu_w, sd_w = np.mean(all_wgi), np.std(all_wgi)

for r in df:
    s = r['lam_b']
    if r['in_conf_2025']:
        s += 0.15
    elif r['last_war_end'] and (2025 - r['last_war_end']) < 3:
        s += 0.05
    if r['iso'] in sat_std:
        s += 0.10 * (sat_std[r['iso']] - mu_s) / sd_s
    if r['iso'] in gdp:
        s += -0.08 * (np.log(gdp[r['iso']][1]) - mu_g) / sd_g
    if r['iso'] in wgi:
        s += -0.08 * (wgi[r['iso']][1] - mu_w) / sd_w
    r['risk'] = s

df = sorted(df, key=lambda r: -r['risk'])

# ---------- 7. 分层输出 ----------
tierA = [r for r in df if r['in_conf_2025']]
tierB = [r for r in df if not r['in_conf_2025'] and r['lam_b'] > 0]
tierC = [r for r in df if r['lam_b'] == 0 and not r['in_conf_2025']]

def show(tier, name, n=12):
    print(f"\n=== {name} (n={len(tier)}) ===")
    print(f"{'ISO':5s} {'risk':>7s} {'λ_b':>6s} {'战年':>4s} {'2025':>5s} {'末战':>5s} {'sat_std':>7s}")
    for r in tier[:n]:
        ss = f"{sat_std[r['iso']]:.2f}" if r['iso'] in sat_std else "  -  "
        le = str(r['last_war_end']) if r['last_war_end'] else "  -  "
        print(f"{r['iso']:5s} {r['risk']:7.3f} {r['lam_b']:6.3f} {r['n_war_years']:4d} "
              f"{'冲突' if r['in_conf_2025'] else '和平':>5s} {le:>5s} {ss:>7s}")

show(tierA, "Tier A: 当前冲突中 (最可能继续/复发)")
show(tierB, "Tier B: 历史高λ_b + 当前和平 (最可能新爆发)")
show(tierC, "Tier C: 无冲突史 + 结构脆弱 (潜在首爆, 外推)", n=8)

# 保存
out = dict(
    n_total=len(df),
    tierA=[{k: r[k] for k in ('iso', 'risk', 'lam_b', 'n_war_years', 'in_conf_2025', 'last_war_end')} for r in tierA],
    tierB=[{k: r[k] for k in ('iso', 'risk', 'lam_b', 'n_war_years', 'last_war_end')} for r in tierB],
    tierC=[{k: r[k] for k in ('iso', 'risk', 'lam_b', 'n_war_years')} for r in tierC],
    note="风险=λ_b+状态项+结构修正(弱权重); 结构修正基于探针⑯ p=0.176 不显著, 仅作软排序",
)
with open('probe17_results.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False, default=str)
print("\n[OK] probe17_results.json 已保存")
