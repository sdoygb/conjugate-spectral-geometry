#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针⑤：社会版三尺度统计刚性——世界银行面板数据的纤维化判别
设计（对应探针③扩展2的 std(m) 标度律）：
  纤维 = 区域（7 个高层纤维）
  微观随机点 = 国家（区域内 n_r 个）
  时间 = 1960-2023（国家长期水平 μ_c = 时间均值）
  集体量 = 区域均值 M_r
判别规则（来自探针③扩展）：刚性 = 集体量被结构锁定（涨落不随微观细节收缩）；
随机 = 集体量只是微观平均（涨落 ~1/√n）。
检验1：国家长期水平排序的时间稳定性（Spearman ρ 前/后半）
检验2：方差分解 η² = SSB/SST（区域间差异 vs 区域内差异）——刚性层次 vs 随机
检验3：区域均值的时间稳定性（前/后半 ρ）——集体量是否被区域结构锁定
"""
import json, math
import numpy as np
from collections import defaultdict

def spearman_rho(x, y):
    """纯 numpy Spearman 秩相关（避免依赖 scipy）"""
    def rank(v):
        order = np.argsort(np.argsort(v)).astype(float)
        # 处理并列：用平均秩近似
        return order
    rx, ry = rank(x), rank(y)
    rx = rx - rx.mean(); ry = ry - ry.mean()
    denom = math.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / denom) if denom > 0 else float('nan')

def load_indicator(fname):
    rows = json.load(open(fname))[1]
    out = defaultdict(dict)  # iso3 -> {year: value}
    for r in rows:
        iso = r.get('countryiso3code')
        if not iso or r.get('value') is None:
            continue
        try:
            out[iso][int(r['date'])] = float(r['value'])
        except (TypeError, ValueError):
            continue
    return out

def country_meta(fname):
    meta = {}
    for c in json.load(open(fname))[1]:
        iso = c.get('id')
        if not iso: continue
        reg = c.get('region', {}).get('value')
        inc = c.get('incomeLevel', {}).get('value')
        if reg and 'Not classified' not in (reg or ''):
            meta[iso] = {'region': reg.strip(), 'income': inc.strip() if inc else ''}
    return meta

def long_mean(series, y0=1960, y1=2023):
    vals = [v for y, v in series.items() if y0 <= y <= y1 and v == v]
    return float(np.mean(vals)) if vals else float('nan')

def bootstrap_subset_std(values, n_sub, n_rep=2000, seed=42):
    """随机抽 n_sub 个元素的均值 std——随机预期 ~σ/√n"""
    rng = np.random.default_rng(seed)
    vals = np.array(values)
    means = np.array([rng.choice(vals, n_sub, replace=False).mean() for _ in range(n_rep)])
    return float(means.std())

def main():
    fert = load_indicator('wb_fertility.json')
    life = load_indicator('wb_life.json')
    meta = country_meta('wb_countries.json')

    # 匹配：只保留有区域元数据的国家
    iso3_to_name = {c['id']: c['name'] for c in json.load(open('wb_countries.json'))[1]}

    # 国家长期水平
    records = []
    for iso, series in fert.items():
        if iso not in meta: continue
        if meta[iso]['region'] == 'Aggregates': continue  # 排除区域聚合体
        mu = long_mean(series)
        if not math.isnan(mu):
            records.append((iso, meta[iso]['region'], mu))
    print(f"== 数据概况：{len(records)} 个国家（生育率长期均值 1960-2023），"
          f"{len(set(r[1] for r in records))} 个区域")

    from collections import Counter
    reg_counts = Counter(r[1] for r in records)
    for reg, n in sorted(reg_counts.items(), key=lambda x: -x[1]):
        print(f"   {reg}: {n} 国")

    # ---------- 检验1：长期排序的时间稳定性 ----------
    print("\n== 检验1：国家长期水平排序的时间稳定性（Spearman ρ：前半1960-1990 vs 后半1991-2023）==")
    pairs = []
    for iso, reg, _ in records:
        s = fert[iso]
        h1 = long_mean(s, 1960, 1990)
        h2 = long_mean(s, 1991, 2023)
        if not math.isnan(h1) and not math.isnan(h2):
            pairs.append((h1, h2))
    if len(pairs) > 10:
        h1 = np.array([p[0] for p in pairs]); h2 = np.array([p[1] for p in pairs])
        rho = spearman_rho(h1, h2)
        print(f"   全部国家 n={len(pairs)}: ρ = {rho:.4f}  {'→ 排序高度稳定（结构锁定）' if rho > 0.7 else '→ 排序漂移（随机）'}")
        # 分区域
        for reg, n in sorted(reg_counts.items(), key=lambda x: -x[1]):
            if n < 6: continue
            rp = []
            for iso, r_, _ in records:
                if r_ != reg: continue
                s = fert[iso]
                a = long_mean(s, 1960, 1990); b = long_mean(s, 1991, 2023)
                if not math.isnan(a) and not math.isnan(b): rp.append((a, b))
            if len(rp) >= 6:
                a = np.array([p[0] for p in rp]); b = np.array([p[1] for p in rp])
                print(f"   {reg[:40]:42s} n={len(rp):3d}  ρ = {spearman_rho(a,b):.4f}")

    # ---------- 检验2：方差分解（区域间 vs 区域内） ----------
    print("\n== 检验2：方差分解 η² = SSB/SST（区域间差异 vs 区域内差异）==")
    mu_all = np.array([r[2] for r in records])
    reg_list = sorted(set(r[1] for r in records))
    grand = mu_all.mean()
    ssb = 0.0; ssw = 0.0
    for reg in reg_list:
        vals = np.array([r[2] for r in records if r[1] == reg])
        n = len(vals)
        ssb += n * (vals.mean() - grand) ** 2
        ssw += ((vals - vals.mean()) ** 2).sum()
    sst = ssb + ssw
    eta2 = ssb / sst
    print(f"   SSB(区域间) = {ssb:.1f}, SSW(区域内) = {ssw:.1f}, SST = {sst:.1f}")
    print(f"   η² = {eta2:.4f}  {'→ 集体规律=区域结构主导（刚性层次）' if eta2 > 0.5 else '→ 区域内随机主导'}")

    # 判别对照：区域内 bootstrap 子样本均值涨落 vs 随机预期 σ/√n
    print("\n   （判别对照：区域内随机抽 n 国的均值涨落 vs 随机预期 σ/√n）")
    for reg in reg_list:
        vals = np.array([r[2] for r in records if r[1] == reg])
        n = len(vals)
        if n < 8: continue
        sigma = vals.std(ddof=1)
        for n_sub in (3, 6, min(10, n)):
            if n_sub >= n: continue
            obs = bootstrap_subset_std(vals, n_sub)
            pred = sigma / math.sqrt(n_sub)
            ratio = obs / pred if pred > 0 else float('nan')
            flag = '≈随机预期(CLT)' if abs(ratio - 1) < 0.15 else ('< 随机预期（超刚性）' if ratio < 0.85 else '> 随机预期')
            print(f"   {reg[:38]:40s} n={n:3d} σ={sigma:.3f}  n_sub={n_sub:2d}: obs={obs:.4f} pred={pred:.4f} 比值={ratio:.2f} {flag}")

    # ---------- 检验3：区域均值的时间稳定性 ----------
    print("\n== 检验3：区域均值的时间稳定性（前/后半区域均值 Spearman ρ）==")
    reg_h = []
    for reg in reg_list:
        vals = np.array([r[2] for r in records if r[1] == reg])
        if len(vals) < 5: continue
        h1 = []; h2 = []
        for iso, r_, _ in records:
            if r_ != reg: continue
            s = fert[iso]
            a = long_mean(s, 1960, 1990); b = long_mean(s, 1991, 2023)
            if not math.isnan(a) and not math.isnan(b):
                h1.append(a); h2.append(b)
        if len(h1) >= 5:
            reg_h.append((reg, np.mean(h1), np.mean(h2)))
    if len(reg_h) >= 4:
        a = np.array([p[1] for p in reg_h]); b = np.array([p[2] for p in reg_h])
        rho = spearman_rho(a, b)
        print(f"   区域数 n={len(reg_h)}: ρ(区域均值 前/后半) = {rho:.4f}")
        for reg, m1, m2 in sorted(reg_h, key=lambda x: x[1]):
            print(f"   {reg[:40]:42s} 前={m1:.2f} 后={m2:.2f}  Δ={m2-m1:+.2f}")

    # ---------- 补充：预期寿命的同一套检验（稳定性交叉验证） ----------
    print("\n== 补充：预期寿命（SP.DYN.LE00.IN）排序稳定性交叉验证 ==")
    pairs_l = []
    for iso, reg, _ in records:
        s = life.get(iso, {})
        h1 = long_mean(s, 1960, 1990); h2 = long_mean(s, 1991, 2023)
        if not math.isnan(h1) and not math.isnan(h2):
            pairs_l.append((h1, h2))
    if len(pairs_l) > 10:
        a = np.array([p[0] for p in pairs_l]); b = np.array([p[1] for p in pairs_l])
        rho = spearman_rho(a, b)
        print(f"   全部国家 n={len(pairs_l)}: ρ = {rho:.4f}")

if __name__ == '__main__':
    main()
