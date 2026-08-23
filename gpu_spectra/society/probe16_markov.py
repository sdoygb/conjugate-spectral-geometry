#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑯：和平↔战争 两态 Markov 模型 + 破缺判别
================================================
几何论映射：
  和平态 P = 纤维化锁定态（耦合完整，宏观速率锁定）
  战争态 W = 破缺事件（耦合断裂，涨落恢复 CLT）
  转移率：λ_b = P→W（破缺率），λ_r = W→P（重构率）
检验：
  (1) 段长度分布 vs 几何（无记忆）——和平段应≈几何（泊松破缺），冲突段偏离=自持
  (2) 平稳分布 π_W 理论 vs 实际
  (3) 自相关 C(Δt) 指数衰减，弛豫时间 τ = 1/(λ_b+λ_r)
  (4) 破缺判别：λ_b × 国内满意度 std（纤维化完整度代理）正相关
数据：UCDP/PRIO v26.1 (1946-2025) + WVS Wave7 满意度
"""
import pandas as pd
import numpy as np
import json
from scipy import stats

np.random.seed(42)

# ---------- 1. 状态序列构建 ----------
df = pd.read_csv('UcdpPrioConflict_v26_1.csv', encoding='latin-1')
years = np.arange(1946, 2026)

# 拆分多国 location
rows = []
for _, r in df.iterrows():
    for loc in str(r['location']).split(','):
        loc = loc.strip()
        if loc:
            rows.append({'country': loc, 'year': r['year']})
conf = pd.DataFrame(rows)
conf = conf.drop_duplicates(subset=['country', 'year'])
print(f"冲突记录: {len(conf)} 国家-年, 国家数: {conf['country'].nunique()}")

# 每国 80 年状态序列
countries = sorted(conf['country'].unique())
states = {}
for c in countries:
    cy = set(conf[conf['country'] == c]['year'])
    states[c] = np.array([1 if y in cy else 0 for y in years])

# ---------- 2. 段长度统计 ----------
def get_segments(seq):
    """返回 (和平段长度列表, 冲突段长度列表)"""
    peace, war = [], []
    cur, cur_len = seq[0], 1
    for s in seq[1:]:
        if s == cur:
            cur_len += 1
        else:
            (peace if cur == 0 else war).append(cur_len)
            cur, cur_len = s, 1
    (peace if cur == 0 else war).append(cur_len)
    return peace, war

all_peace, all_war = [], []
per_country = {}
for c in countries:
    p, w = get_segments(states[c])
    all_peace.extend(p)
    all_war.extend(w)
    per_country[c] = {'peace': p, 'war': w}

all_peace = np.array(all_peace)
all_war = np.array(all_war)
print(f"\n段统计: 和平段 n={len(all_peace)} (mean={all_peace.mean():.2f}), 冲突段 n={len(all_war)} (mean={all_war.mean():.2f})")

# ---------- 3. 转移率与平稳分布 ----------
lam_b = 1.0 / all_peace.mean()      # 破缺率 (年^-1)
lam_r = 1.0 / all_war.mean()        # 重构率 (年^-1)
pi_W_theory = lam_b / (lam_b + lam_r)
pi_W_actual = conf.groupby('country').size().sum() / (len(countries) * len(years))
print(f"\nλ_b = {lam_b:.4f} /年  (平均和平段 {all_peace.mean():.2f} 年)")
print(f"λ_r = {lam_r:.4f} /年  (平均冲突段 {all_war.mean():.2f} 年)")
print(f"π_W 理论 = {pi_W_theory:.4f} vs 实际 = {pi_W_actual:.4f}")

# ---------- 4. 段长度分布 vs 几何分布 ----------
def ks_geometric(segments, name):
    """检验段长度是否服从几何分布（无记忆）"""
    p = 1.0 / segments.mean()
    # 几何分布 CDF: 1-(1-p)^k, k=1,2,...
    rv = stats.geom(p)
    ks = stats.kstest(segments, rv.cdf)
    # 尾重指标：P(段 > 2*mean) 观测 vs 几何预言
    obs_tail = (segments > 2 * segments.mean()).mean()
    theo_tail = 1 - rv.cdf(2 * segments.mean())
    print(f"{name}: n={len(segments)}, mean={segments.mean():.2f}, p_geom={p:.4f}")
    print(f"  KS: D={ks.statistic:.4f}, p={ks.pvalue:.2e}  (>0.05 = 不拒绝几何)")
    print(f"  尾重: 观测 P(>2μ)={obs_tail:.4f} vs 几何预言 {theo_tail:.4f}  (观测>预言 = 重尾/自持)")
    return ks

print("\n--- 段长度分布检验 ---")
ks_p = ks_geometric(all_peace, "和平段（破缺等待时间）")
ks_w = ks_geometric(all_war, "冲突段（重构时间）")


# ---------- 4.5 异质性控制：按国家检验段分布 ----------
print("\n--- 异质性控制（按国家） ---")
hetero_peace, hetero_war = [], []
for c in countries:
    p_seg = np.array(per_country[c]['peace'])
    w_seg = np.array(per_country[c]['war'])
    if len(p_seg) >= 5:
        ks_c = stats.kstest(p_seg, stats.geom(1.0/p_seg.mean()).cdf)
        hetero_peace.append(ks_c.pvalue)
    if len(w_seg) >= 5:
        ks_c = stats.kstest(w_seg, stats.geom(1.0/w_seg.mean()).cdf)
        hetero_war.append(ks_c.pvalue)
import numpy as _np
hetero_peace = _np.array(hetero_peace); hetero_war = _np.array(hetero_war)
print(f"和平段: {len(hetero_peace)} 国(≥5段) 中 {int((hetero_peace<0.05).sum())} 国拒绝几何 ({100*(hetero_peace<0.05).mean():.0f}%)")
print(f"冲突段: {len(hetero_war)} 国(≥5段) 中 {int((hetero_war<0.05).sum())} 国拒绝几何 ({100*(hetero_war<0.05).mean():.0f}%)")
# 单国拒绝率 vs 5% 名义水平 → 若≈5% 则全局重尾纯系异质性；若≫5% 则有内在记忆
# ---------- 5. 自相关函数 ----------
def autocorr_state(seq, max_lag=30):
    s = seq - seq.mean()
    v = (s * s).mean()
    out = []
    for lag in range(max_lag + 1):
        out.append((s[:len(s)-lag] * s[lag:]).mean() / v if lag > 0 else 1.0)
    return np.array(out)

# 池化所有国家的自相关（按国家内计算再平均）
lags = np.arange(31)
ac_all = np.zeros(31)
for c in countries:
    ac_all += autocorr_state(states[c], 30)
ac_all /= len(countries)

# 两态 Markov 理论自相关: C(Δt) = exp(-(λ_b+λ_r)|Δt|)
lam_sum = lam_b + lam_r
ac_theory = np.exp(-lam_sum * lags)
# 拟合实际衰减率（从 lag1-10 线性拟合 log C）
slope, intercept = np.polyfit(lags[1:11], np.log(np.clip(ac_all[1:11], 1e-9, None)), 1)
tau_fit = -1.0 / slope
tau_theory = 1.0 / lam_sum
print(f"\n--- 自相关 ---")
print(f"理论弛豫 τ = 1/(λ_b+λ_r) = {tau_theory:.2f} 年")
print(f"拟合弛豫 τ_fit = {tau_fit:.2f} 年 (lag 1-10 log 线性拟合)")
print(f"C(1)={ac_all[1]:.4f}, C(5)={ac_all[5]:.4f}, C(10)={ac_all[10]:.4f}, C(20)={ac_all[20]:.4f}")
print(f"理论 C(1)={ac_theory[1]:.4f}, C(5)={ac_theory[5]:.4f}, C(10)={ac_theory[10]:.4f}, C(20)={ac_theory[20]:.4f}")

# ---------- 6. 破缺判别：λ_b × 满意度国内 std ----------
# WVS Wave7 满意度（与 probe6 相同逻辑：Q49 生活满意度 1-10）
wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', low_memory=False)
sat_col = None
for cand in ['Q49', 'Q50']:
    if cand in wvs.columns:
        sat_col = cand
        break
print(f"\n满意度变量: {sat_col}")
wvs_sat = wvs[['B_COUNTRY_ALPHA', sat_col]].dropna()
wvs_sat = wvs_sat[wvs_sat[sat_col] > 0]  # 去除缺失编码
wvs_sat = wvs_sat[wvs_sat[sat_col] <= 10]

# 每国满意度国内 std + mean
sat_stats = wvs_sat.groupby('B_COUNTRY_ALPHA')[sat_col].agg(['mean', 'std', 'count']).reset_index()
sat_stats.columns = ['alpha', 'sat_mean', 'sat_std', 'sat_n']
sat_stats = sat_stats[sat_stats['sat_n'] >= 30]

# 国家名映射：UCDP location → ISO3（ucdp2iso.json 手工表）
import json as _json
rev = _json.load(open('ucdp2iso.json'))

# 每国 λ_b 估计
rows_lam = []
for c in countries:
    p_seg = per_country[c]['peace']
    lam_b_i = 1.0 / np.mean(p_seg) if len(p_seg) > 0 else None
    alpha = rev.get(c)
    rows_lam.append({'ucdp': c, 'alpha': alpha, 'lam_b': lam_b_i,
                     'mean_peace': np.mean(p_seg) if len(p_seg) > 0 else None,
                     'n_war_years': int(np.sum(states[c]))})
lam_df = pd.DataFrame(rows_lam)

# 合并满意度
merged = lam_df.merge(sat_stats, on='alpha', how='inner')
merged = merged.dropna(subset=['lam_b'])
print(f"\n破缺判别样本: {len(merged)} 国 (UCDP∩WVS)")

# 相关：λ_b × sat_std（国家内离散度 = 纤维化完整度代理）
if len(merged) >= 10:
    r_b, p_b = stats.spearmanr(merged['lam_b'], merged['sat_std'])
    print(f"λ_b × 满意度国内std: ρ={r_b:.3f}, p={p_b:.3f}")
    r_b2, p_b2 = stats.spearmanr(merged['lam_b'], merged['sat_mean'])
    print(f"λ_b × 满意度均值: ρ={r_b2:.3f}, p={p_b2:.3f}")
    # 有冲突 vs 无冲突国的 sat_std 对照
    war_flag = merged['n_war_years'] > 0
    if war_flag.sum() > 5 and (~war_flag).sum() > 5:
        u_stat, u_p = stats.mannwhitneyu(merged.loc[war_flag, 'sat_std'], merged.loc[~war_flag, 'sat_std'])
        print(f"冲突国 sat_std={merged.loc[war_flag,'sat_std'].mean():.3f} vs 和平国={merged.loc[~war_flag,'sat_std'].mean():.3f}, MWU p={u_p:.3f}")

# ---------- 7. 输出 ----------
results = {
    'n_countries': len(countries),
    'n_years': len(years),
    'lam_b': lam_b, 'lam_r': lam_r,
    'mean_peace_len': float(all_peace.mean()), 'mean_war_len': float(all_war.mean()),
    'pi_W_theory': pi_W_theory, 'pi_W_actual': pi_W_actual,
    'ks_peace': {'D': ks_p.statistic, 'p': ks_p.pvalue},
    'ks_war': {'D': ks_w.statistic, 'p': ks_w.pvalue},
    'tail_peace_obs': float((all_peace > 2*all_peace.mean()).mean()),
    'tail_war_obs': float((all_war > 2*all_war.mean()).mean()),
    'tau_theory': tau_theory, 'tau_fit': tau_fit,
    'ac_lags': lags.tolist(), 'ac_obs': ac_all.tolist(), 'ac_theory': ac_theory.tolist(),
}
if len(merged) >= 10:
    results['breakdown'] = {'rho_lamB_satStd': float(r_b), 'p_lamB_satStd': float(p_b),
                            'rho_lamB_satMean': float(r_b2), 'p_lamB_satMean': float(p_b2)}
    results['n_breakdown'] = len(merged)
with open('probe16_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
print("\n[OK] probe16_results.json 已保存")
