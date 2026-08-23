#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针⑲：2026 结构诊断——当前全球破缺水平 vs 理论平稳分布，东亚东南亚区域状态
核心问题：当前世界是否处于"补缺窗口"（结构诊断），而非"预言 2026 年出现谁"
"""
import pandas as pd, numpy as np, json, sys

BASE = ""

# ---------- 1. 全球冲突密度：当前 vs 历史 vs 理论平稳分布 ----------
ucdp = pd.read_csv(BASE + "UcdpPrioConflict_v26_1.csv", low_memory=False)
# 每年有冲突的国家数（location 去重）
years = range(1946, 2026)
n_conf_per_year = []
for y in years:
    sub = ucdp[ucdp["year"] == y]
    n_conf_per_year.append(sub["location"].nunique())

df = pd.DataFrame({"year": list(years), "n_conf": n_conf_per_year})
df["n_conf_frac"] = df["n_conf"] / 194  # UCDP 全球约 194 国

hist_mean = df[df["year"] <= 2019]["n_conf_frac"].mean()
recent_mean = df[df["year"] >= 2020]["n_conf_frac"].mean()
last3 = df[df["year"] >= 2023]["n_conf_frac"].mean()

# 理论平稳分布（探针⑯）：λ_b=0.061/年, λ_r=0.190/年 → π_C = λ_b/(λ_b+λ_r)
lb, lr = 0.061, 0.190
pi_C_theory = lb / (lb + lr)

# ---------- 2. 东亚东南亚区域状态 ----------
EAST_ASIA = ["China","Taiwan","Japan","South Korea","North Korea","Mongolia"]
SE_ASIA = ["Myanmar","Thailand","Vietnam","Cambodia","Laos","Philippines","Indonesia",
           "Malaysia","Singapore","Brunei","Timor-Leste"]
SOUTH_ASIA_E = ["Bangladesh","Nepal","Bhutan","India","Pakistan","Sri Lanka"]
REGION = EAST_ASIA + SE_ASIA + SOUTH_ASIA_E

print("="*70)
print("探针⑲：2026 结构诊断——当前世界是否处于补缺窗口？")
print("="*70)

print("\n【1】全球冲突密度（有冲突国家比例）")
print(f"  1946-2019 历史均值 : {hist_mean:.4f}")
print(f"  2020-2025 均值     : {recent_mean:.4f}")
print(f"  2023-2025 均值     : {last3:.4f}")
print(f"  2025 当年          : {df[df.year==2025].n_conf_frac.values[0]:.4f}")
print(f"  探针⑯ 理论平稳分布 π_C = λ_b/(λ_b+λ_r) = {pi_C_theory:.4f}")

# 近 5 年东亚东南亚冲突
sub5 = ucdp[ucdp["year"] >= 2021]
reg_conf = sub5[sub5["location"].isin(REGION)]
reg_conf_by_country = reg_conf.groupby("location")["year"].agg(["min","max","count"])

print("\n【2】东亚/东南亚/南亚 2021-2025 冲突状态（UCDP 门槛 ≥25 战死/年）")
if len(reg_conf_by_country) == 0:
    print("  该区域近 5 年无 UCDP 门槛冲突")
else:
    for loc, row in reg_conf_by_country.iterrows():
        print(f"  {loc:<12} 冲突年 {int(row['count'])}  区间 {int(row['min'])}-{int(row['max'])}")

# 区域内近5年 vs 区域外
reg_n = len(REGION)
reg_conf_n = reg_conf["location"].nunique()
print(f"\n  区域 {reg_n} 国中 {reg_conf_n} 国有冲突 = {reg_conf_n/reg_n:.3f}")

# ---------- 3. 结构脆弱度：WVS 满意度国内 std（东亚东南亚） ----------
print("\n【3】结构脆弱度：WVS Wave7 生活满意度国内 std（探针⑰ 口径）")
wvs = pd.read_csv(BASE + "WVS_Cross-National_Wave_7_csv_v6_0.csv", low_memory=False,
                  usecols=lambda c: c in ("COW_ALPHA","Q49"))
wvs = wvs.rename(columns={"COW_ALPHA": "cc", "Q49": "sat"})
wvs = wvs[(wvs["sat"] >= 1) & (wvs["sat"] <= 10)]

# COW_ALPHA 映射到区域名单
alpha_map = {"CHN":"China","TWN":"Taiwan","JPN":"Japan","KOR":"South Korea","PRK":"North Korea",
             "MNG":"Mongolia","MMR":"Myanmar","THA":"Thailand","VNM":"Vietnam","KHM":"Cambodia",
             "LAO":"Laos","PHL":"Philippines","IDN":"Indonesia","MYS":"Malaysia","SGP":"Singapore",
             "BRN":"Brunei","TLS":"Timor-Leste","BGD":"Bangladesh","NPL":"Nepal","BTN":"Bhutan",
             "IND":"India","PAK":"Pakistan","LKA":"Sri Lanka"}
wvs["region_name"] = wvs["cc"].map(alpha_map)
wvs_reg = wvs[wvs["region_name"].isin(REGION)].dropna(subset=["region_name"])
if len(wvs_reg) > 0:
    std_by_country = wvs_reg.groupby("region_name")["sat"].agg(["std","count"])
    std_by_country = std_by_country[std_by_country["count"] > 100].sort_values("std", ascending=False)
    print(f"  该区域 WVS 有数据国家（n≥100）：{len(std_by_country)}")
    for name, row in std_by_country.head(10).iterrows():
        print(f"  {name:<12} std={row['std']:.3f}  n={int(row['count'])}")
    all_std = wvs.groupby("cc")["sat"].agg(["std","count"])
    all_std = all_std[all_std["count"] > 100]
    print(f"\n  区域 std 中位数 {std_by_country['std'].median():.3f} vs 全球中位数 {all_std['std'].median():.3f}")
    print(f"  区域 std 均值   {std_by_country['std'].mean():.3f} vs 全球均值   {all_std['std'].mean():.3f}")

# ---------- 4. 历史对照：轴心时代补缺窗口的特征 ----------
print("\n【4】轴心时代补缺窗口的判据（探针⑱）对照当前")
print("  判据1 破缺密集期（十六大国兼并战争）→ 当前全球冲突密度是否处于历史高位？")
print(f"        当前(2023-25) {last3:.3f} vs 历史均值 {hist_mean:.3f} → 比值 {last3/hist_mean:.2f}x")
print("  判据2 结构脆弱（满意度 std 高）→ 区域 std vs 全球")
print("  判据3 认知层操作先于制度层补缺 → 不可由数据诊断，留作开放")

# ---------- 5. 结论框架 ----------
print("\n【5】诊断结论框架")
print(f"  理论平稳战争比例 π_C = {pi_C_theory:.3f}（探针⑯）")
print(f"  当前实际战争比例 = {df[df.year==2025].n_conf_frac.values[0]:.3f} → "
      f"{'高于' if df[df.year==2025].n_conf_frac.values[0] > pi_C_theory else '低于/接近'}理论值")

result = {
    "hist_mean_frac": float(hist_mean), "recent_mean_frac": float(recent_mean),
    "last3_frac": float(last3), "frac_2025": float(df[df.year==2025].n_conf_frac.values[0]),
    "pi_C_theory": float(pi_C_theory),
    "east_se_asia_conflicts_2021_25": {k: int(v["count"]) for k, v in reg_conf_by_country.iterrows()},
}
with open(BASE + "probe19_results.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n已保存 probe19_results.json")
