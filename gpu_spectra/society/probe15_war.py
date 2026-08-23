#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe15_war.py — 战争作为集体输出: UCDP v26.1 战死/冲突数据
设计:
  A. 时间锁定检验: 1946-2023 分前后两半, 国家战死/冲突年数排序稳定性 ρ
     (对应探针⑤/⑪: 若战争倾向是结构锁定的集体量, ρ 应显著 > 0;
      若战争本质随机, ρ≈0)
  B. 破缺判别: 国家 WVS 个体离散度(满意度 std) × 冲突卷入(冲突年数/战死)
     (对应探针④: 纤维内破缺 → 宏观失稳)
"""
import csv, json
from collections import defaultdict
from statistics import mean, pstdev
import numpy as np
from scipy.stats import spearmanr

# ---------- ISO alpha-2 -> GW 码 (UCDP gwno) ----------
ISO2GW = {
    # Europe
    'AND':None,'ARM':371,'CYP':352,'CZE':316,'DEU':260,'GBR':200,'GRC':350,
    'NIR':200,'NLD':210,'ROU':360,'RUS':365,'SRB':345,'SVK':317,'TUR':640,'UKR':369,
    # Asia
    'BGD':771,'CHN':710,'HKG':710,'IDN':850,'IND':750,'IRN':630,'IRQ':645,'JPN':740,
    'KAZ':705,'KGZ':703,'KOR':732,'LBN':660,'MAC':710,'MDV':781,'MMR':775,'MNG':712,
    'MYS':820,'PAK':770,'PHL':840,'SGP':830,'THA':800,'TJK':702,'TWN':713,'UZB':704,
    'VNM':816,'JOR':663,
    # Africa
    'EGY':651,'ETH':530,'KEN':501,'LBY':620,'MAR':600,'NGA':475,'TUN':616,'ZWE':552,
    # Americas
    'ARG':160,'BOL':145,'BRA':140,'CAN':20,'CHL':155,'COL':100,'ECU':130,'GTM':90,
    'MEX':70,'NIC':93,'PER':135,'PRI':2,'URY':165,'USA':2,'VEN':101,
    # Oceania
    'AUS':900,'NZL':920,
}
WVS_ISO = sorted(ISO2GW.keys())
GW2ISO = {}
for iso, gw in ISO2GW.items():
    if gw is not None:
        GW2ISO.setdefault(gw, []).append(iso)

def split_gwno(s):
    """UCDP gwno 字段可能逗号分隔多值"""
    if not s or s.strip() == '':
        return []
    return [int(x.strip()) for x in s.split(',') if x.strip()]

def load_battledeaths():
    """(gwno, year) -> bd_best 求和; 多个地点码拆开"""
    agg = defaultdict(int)
    with open('BattleDeaths_v26_1.csv', newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                bd = int(float(row['bd_best']))
                yr = int(row['year'])
            except (ValueError, KeyError):
                continue
            gws = split_gwno(row['gwno_loc'])
            if not gws:
                gws = split_gwno(row['gwno_battle'])
            for gw in gws:
                agg[(gw, yr)] += bd
    return agg

def load_conflicts():
    """(gwno, year) -> (max_intensity, conflict_flag); 地点码拆开"""
    agg = defaultdict(lambda: [0, 0])  # (max_intensity, any_conflict)
    with open('UcdpPrioConflict_v26_1.csv', newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                yr = int(row['year'])
                inten = int(row['intensity_level'])
            except (ValueError, KeyError):
                continue
            gws = split_gwno(row['gwno_loc'])
            for gw in gws:
                cur = agg[(gw, yr)]
                cur[0] = max(cur[0], inten)
                cur[1] = 1
    return agg

def spearman(a, b):
    if len(a) < 3:
        return 0.0
    rho, _ = spearmanr(a, b)
    return float(rho)

# ---------- 加载 ----------
print("加载 BattleDeaths ...")
bd = load_battledeaths()
print("加载 UcdpPrioConflict ...")
cf = load_conflicts()
print(f"  战死条目: {len(bd)}, 冲突条目: {len(cf)}")

# ---------- 66 国聚合 ----------
stats = {}
for iso in WVS_ISO:
    gw = ISO2GW[iso]
    if gw is None:
        stats[iso] = dict(gw=None, total_bd=0, conflict_years=0, war_years=0,
                          first_conflict=None, last_conflict=None,
                          bd_by_period={'early': 0, 'late': 0},
                          cy_by_period={'early': 0, 'late': 0})
        continue
    total = sum(v for (g, y), v in bd.items() if g == gw)
    cys = [y for (g, y) in cf if g == gw and cf[(g, y)][1]]
    wys = [y for (g, y) in cf if g == gw and cf[(g, y)][0] >= 2]
    early_bd = sum(v for (g, y), v in bd.items() if g == gw and y <= 1984)
    late_bd = sum(v for (g, y), v in bd.items() if g == gw and y >= 1985)
    early_cy = sum(1 for y in cys if y <= 1984)
    late_cy = sum(1 for y in cys if y >= 1985)
    stats[iso] = dict(
        gw=gw, total_bd=total, conflict_years=len(cys), war_years=len(wys),
        first_conflict=min(cys) if cys else None,
        last_conflict=max(cys) if cys else None,
        bd_by_period={'early': early_bd, 'late': late_bd},
        cy_by_period={'early': early_cy, 'late': late_cy},
    )

# ---------- A. 时间锁定检验 ----------
# 有冲突的国家子集 (至少 1 个冲突年)
conflicted = [iso for iso in WVS_ISO if stats[iso]['conflict_years'] > 0]
n_conflicted = len(conflicted)
print(f"\n[A] 时间锁定检验: 66 国中 {n_conflicted} 国有冲突记录 (1946-2023)")

# 战死数: 前后半排序稳定性 (只用两半都有数据的国家)
both_bd = [iso for iso in conflicted
           if stats[iso]['bd_by_period']['early'] > 0 and stats[iso]['bd_by_period']['late'] > 0]
if len(both_bd) >= 3:
    rho_bd = spearman([stats[i]['bd_by_period']['early'] for i in both_bd],
                      [stats[i]['bd_by_period']['late'] for i in both_bd])
    # 置换检验
    rng = np.random.default_rng(42)
    nulls = []
    for _ in range(2000):
        late_p = rng.permutation([stats[i]['bd_by_period']['late'] for i in both_bd])
        nulls.append(spearman([stats[i]['bd_by_period']['early'] for i in both_bd], late_p))
    nulls = np.array(nulls)
    p_val = float((np.abs(nulls) >= abs(rho_bd)).mean())
    print(f"  战死数(前/后半) n={len(both_bd)}: ρ={rho_bd:.4f}, 置换 p={p_val:.4f}, null std={nulls.std():.3f}")
else:
    rho_bd, p_val = None, None
    print(f"  战死数前后半都有数据的国家不足: n={len(both_bd)}")

# 冲突年数: 前后半排序稳定性
both_cy = [iso for iso in conflicted
           if stats[iso]['cy_by_period']['early'] > 0 and stats[iso]['cy_by_period']['late'] > 0]
if len(both_cy) >= 3:
    rho_cy = spearman([stats[i]['cy_by_period']['early'] for i in both_cy],
                      [stats[i]['cy_by_period']['late'] for i in both_cy])
    rng2 = np.random.default_rng(7)
    nulls2 = []
    for _ in range(2000):
        late_p = rng2.permutation([stats[i]['cy_by_period']['late'] for i in both_cy])
        nulls2.append(spearman([stats[i]['cy_by_period']['early'] for i in both_cy], late_p))
    nulls2 = np.array(nulls2)
    p2 = float((np.abs(nulls2) >= abs(rho_cy)).mean())
    print(f"  冲突年数(前/后半) n={len(both_cy)}: ρ={rho_cy:.4f}, 置换 p={p2:.4f}, null std={nulls2.std():.3f}")
else:
    rho_cy, p2 = None, None
    print(f"  冲突年数前后半都有数据的国家不足: n={len(both_cy)}")

# 全体 66 国 (含零): 冲突年数排序稳定性
rho_all = spearman([stats[i]['cy_by_period']['early'] for i in WVS_ISO],
                   [stats[i]['cy_by_period']['late'] for i in WVS_ISO])
print(f"  冲突年数(前/后半) 全体66国(含0): ρ={rho_all:.4f}")

# ---------- B. 破缺判别: WVS 国内离散度 × 冲突 ----------
print("\n[B] 破缺判别: 国家满意度离散度 × 冲突卷入")
CSV_WVS = 'WVS_Cross-National_Wave_7_csv_v6_0.csv'
wvs_std = {}
wvs_mean = {}
with open(CSV_WVS, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    by_c = defaultdict(list)
    for row in r:
        a = row['B_COUNTRY_ALPHA']
        try:
            q50 = int(row['Q50'])
        except ValueError:
            continue
        if 1 <= q50 <= 10:
            by_c[a].append(q50)
for a, vals in by_c.items():
    if a in ISO2GW and len(vals) >= 30:
        wvs_std[a] = pstdev(vals)
        wvs_mean[a] = mean(vals)

common = [a for a in wvs_std if a in stats]
xs = [wvs_std[a] for a in common]
ys_conf = [stats[a]['conflict_years'] for a in common]
ys_bd = [np.log10(stats[a]['total_bd'] + 1) for a in common]
rho_s = spearman(xs, ys_conf)
rho_b = spearman(xs, ys_bd)
print(f"  国家数 n={len(common)}")
print(f"  满意度国内std × 冲突年数: ρ={rho_s:.4f}")
print(f"  满意度国内std × log10(战死+1): ρ={rho_b:.4f}")

# 和平 vs 冲突国家 的国内离散度对比
peace = [wvs_std[a] for a in common if stats[a]['conflict_years'] == 0]
war = [wvs_std[a] for a in common if stats[a]['conflict_years'] > 0]
print(f"  和平国(0冲突) n={len(peace)}: 均值={mean(peace):.4f}" if peace else "  无和平国")
print(f"  冲突国 n={len(war)}: 均值={mean(war):.4f}" if war else "  无冲突国")

# ---------- 输出 ----------
out = dict(
    n_conflicted=n_conflicted,
    time_lock_bd=dict(n=len(both_bd), rho=round(rho_bd, 4) if rho_bd else None,
                      p=round(p_val, 4) if p_val else None) if both_bd else None,
    time_lock_cy=dict(n=len(both_cy), rho=round(rho_cy, 4) if rho_cy else None,
                      p=round(p2, 4) if p2 else None) if both_cy else None,
    time_lock_cy_all66=round(rho_all, 4),
    breakdown=dict(n=len(common),
                   rho_std_conf=round(rho_s, 4), rho_std_bd=round(rho_b, 4),
                   peace_mean=round(mean(peace), 4) if peace else None,
                   war_mean=round(mean(war), 4) if war else None),
    countries={iso: stats[iso] for iso in WVS_ISO},
)
with open('probe15_results.json', 'w') as f:
    json.dump(out, f, indent=1, ensure_ascii=False, default=str)
print("\n已保存 probe15_results.json")
