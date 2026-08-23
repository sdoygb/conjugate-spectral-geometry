#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑩：CEPII GeoDist 地理/结构距离 × 国家满意度差异
与探针⑭（ASJP 语言距离）同口径对照：
  语言距离（结构耦合代理）是排除链上第一个显著预测子（ρ=+0.105, p=0.033）。
  本探针检验：地理邻近（distw）、共同边界（contig）、官方共同语言（comlang_off）、
  族群共同语言（comlang_ethno）、殖民关系（colony）是否更接近"成对耦合配置"。

数据：
  dist_cepii.xls（225 国成对：dist/distw/distwces/contig/comlang_off/comlang_ethno/colony）
  WVS Wave 7 v6.0（Q49 生活满意度 1-10，66 国）

检验：
  [1] Mantel 型：log(distw) × |Δsat| Spearman + 置换零假设（与探针⑭同款）
  [2] distw 三分位 → 平均 |Δsat| 单调性
  [3] 二元结构链接对照：contig / comlang_off / comlang_ethno / colony
      链接内 vs 链接外 |Δsat|（置换 t 检验）
  [4] 对照表：与探针⑭语言距离结果并排
  [5] 偏 Mantel：控制地理距离后，语言距离是否仍显著（残差化 Spearman）
"""
import pandas as pd
import numpy as np
import json, time

def spearman(a, b):
    from scipy.stats import rankdata
    ra = rankdata(a); rb = rankdata(b)
    n = len(a)
    return float(1 - 6 * np.sum((ra - rb)**2) / (n * (n**2 - 1)))

def perm_test(x, y, n_perm=2000, seed=42):
    """Mantel 型置换零假设：固定 x，打乱 y 的行/列（即打乱国家标签）"""
    rho = spearman(x, y)
    rng = np.random.default_rng(seed)
    nulls = []
    for _ in range(n_perm):
        perm = rng.permutation(len(y))
        nulls.append(spearman(x, y[perm]))
    nulls = np.array(nulls)
    z = (rho - nulls.mean()) / nulls.std()
    p = float((np.abs(nulls) >= abs(rho)).mean())
    return rho, z, p, nulls

def perm_t(a, b, n_perm=20000, seed=7):
    """二元链接内 vs 外：均值差的置换检验"""
    da, db = np.asarray(a, float), np.asarray(b, float)
    obs = da.mean() - db.mean()
    pool = np.concatenate([da, db])
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n_perm):
        perm = rng.permutation(len(pool))
        m1 = pool[perm[:len(da)]].mean()
        m2 = pool[perm[len(da):]].mean()
        if abs(m1 - m2) >= abs(obs):
            cnt += 1
    return float(obs), cnt / n_perm

def main():
    t0 = time.time()
    # ---------- WVS7 满意度均值 ----------
    wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', sep=',',
                      usecols=['B_COUNTRY_ALPHA', 'Q49'], encoding='utf-8-sig',
                      dtype={'B_COUNTRY_ALPHA': str, 'Q49': float})
    q = pd.to_numeric(wvs['Q49'], errors='coerce')
    wvs['sat'] = q.where(q >= 1)
    means = wvs.groupby(wvs['B_COUNTRY_ALPHA'].str.strip().str.upper())['sat'].mean()
    print(f'[wvs] 国家数: {len(means)}')

    # ---------- CEPII dist_cepii ----------
    d = pd.read_excel('dist_cepii.xls')
    d['iso_o'] = d['iso_o'].str.strip().str.upper()
    d['iso_d'] = d['iso_d'].str.strip().str.upper()

    # 码表对齐：WVS→CEPII（ROU→ROM 罗马尼亚；SRB→YUG 塞尔维亚(贝尔格莱德距离)；NIR→GBR 北爱尔兰属英国）
    CODE_MAP = {'ROU': 'ROM', 'SRB': 'YUG', 'NIR': 'GBR'}
    means = means.groupby(means.index.map(lambda c: CODE_MAP.get(c, c))).mean()
    means2 = means
    ctrys = sorted(means2.index)
    geo_codes = set(d['iso_o']) | set(d['iso_d'])
    missing = [c for c in ctrys if c not in geo_codes]
    ctrys = [c for c in ctrys if c in geo_codes]
    print(f'[cepii] 国家数: {len(ctrys)}（CEPII 缺失: {missing or "无"}；码映射: {CODE_MAP}）')
    means = means2

    n = len(ctrys)
    D_geo = np.full((n, n), np.nan)
    D_contig = np.zeros((n, n))
    D_comoff = np.zeros((n, n))
    D_cometh = np.zeros((n, n))
    D_colony = np.zeros((n, n))
    pair_map = {(r['iso_o'], r['iso_d']): r for _, r in d.iterrows()}
    for i in range(n):
        for j in range(i + 1, n):
            key = (ctrys[i], ctrys[j])
            r = pair_map.get(key)
            if r is None:
                r = pair_map.get((ctrys[j], ctrys[i]))
            if r is None:
                continue
            dw = r['distw']
            if isinstance(dw, str) and dw.strip() == '.':
                dw = float('nan')
            D_geo[i, j] = D_geo[j, i] = float(dw)
            D_contig[i, j] = D_contig[j, i] = float(r['contig'])
            D_comoff[i, j] = D_comoff[j, i] = float(r['comlang_off'])
            D_cometh[i, j] = D_cometh[j, i] = float(r['comlang_ethno'])
            D_colony[i, j] = D_colony[j, i] = float(r['colony'])

    sat = np.array([means[c] for c in ctrys])
    D_sat = np.abs(sat[:, None] - sat[None, :])
    idx = np.triu_indices(n, 1)

    logd = np.log(D_geo[idx])
    ds = D_sat[idx]
    valid = ~np.isnan(logd)
    logd, ds = logd[valid], ds[valid]
    contig = D_contig[idx][valid].astype(bool)
    comoff = D_comoff[idx][valid].astype(bool)
    cometh = D_cometh[idx][valid].astype(bool)
    colony = D_colony[idx][valid].astype(bool)
    print(f'[pair] 有效成对: {len(ds)} / {len(idx[0])}')

    # [1] Mantel：log(distw) × |Δsat|
    rho1, z1, p1, _ = perm_test(logd, ds)
    print(f'\n=== [1] Mantel：log(地理距离) × |Δ满意度| ===')
    print(f'  ρ = {rho1:+.4f}   z = {z1:+.1f}σ   p = {p1:.4f}')

    # [2] distw 三分位
    q1, q2 = np.quantile(np.exp(logd), [1/3, 2/3])
    dd = np.exp(logd)
    t1 = ds[dd <= q1]; t2 = ds[(dd > q1) & (dd <= q2)]; t3 = ds[dd > q2]
    print(f'\n=== [2] 地理距离三分位 → 平均 |Δ满意度| ===')
    print(f'  T1(近, ≤{q1:.0f}km): mean={t1.mean():.3f}  n={len(t1)}')
    print(f'  T2(中):             mean={t2.mean():.3f}  n={len(t2)}')
    print(f'  T3(远, >{q2:.0f}km): mean={t3.mean():.3f}  n={len(t3)}')

    # [3] 二元结构链接
    print(f'\n=== [3] 结构链接：链接内 vs 链接外 ===')
    res_bin = {}
    for name, mask in [('共同边界 contig', contig), ('官方共同语言', comoff),
                       ('族群共同语言', cometh), ('殖民关系 colony', colony)]:
        if mask.sum() < 5 or (~mask).sum() < 5:
            print(f'  {name}: n 过少 ({mask.sum()})，跳过')
            continue
        obs, pv = perm_t(ds[mask], ds[~mask])
        res_bin[name] = dict(inside=round(float(ds[mask].mean()), 3),
                             outside=round(float(ds[~mask].mean()), 3),
                             n_inside=int(mask.sum()), diff=round(float(obs), 3), p=round(pv, 4))
        print(f'  {name}: 内={ds[mask].mean():.3f} 外={ds[~mask].mean():.3f} '
              f'(Δ={obs:+.3f}, p={pv:.4f}, n内={mask.sum()})')

    # [4] 与探针⑭语言距离对照
    print(f'\n=== [4] 对照表（同口径 Mantel） ===')
    print(f'  语言距离 ASJP (探针⑭): ρ=+0.105  z=+2.1σ  p=0.033')
    print(f'  地理距离 log(distw)   : ρ={rho1:+.4f}  z={z1:+.1f}σ  p={p1:.4f}')

    # [5] 偏 Mantel：控制地理距离后语言距离是否仍显著
    asjp_pair = {}
    if 'probe14_results.json' in __import__('os').listdir('.'):
        pass
    # 语言距离矩阵重建（复用探针⑭的 ldnd——直接加载 lists.txt 重算，保证成对集合一致）
    import re
    from collections import defaultdict
    from probe14_asjp import parse_asjp, ldnd, CTRY_LANG
    langs = parse_asjp('lists.txt')
    n2 = len(ctrys)
    D_lang = np.full((n2, n2), np.nan)
    lang_missing = []
    for i in range(n2):
        if CTRY_LANG.get(ctrys[i]) not in langs:
            lang_missing.append(ctrys[i])
    for i in range(n2):
        for j in range(i + 1, n2):
            la, lb = CTRY_LANG.get(ctrys[i]), CTRY_LANG.get(ctrys[j])
            if la in langs and lb in langs:
                dd2 = ldnd(langs[la], langs[lb])
                if dd2 is not None:
                    D_lang[i, j] = D_lang[j, i] = dd2
    print(f'\n[partial] 语言缺失: {lang_missing or "无"}')
    lg = D_lang[idx][valid]
    ok = ~np.isnan(lg)
    if ok.sum() > 30:
        # 残差化：|Δsat| 对 log(distw) 回归取残差，再与语言距离相关
        X = np.column_stack([np.ones(ok.sum()), logd[ok]])
        beta, *_ = np.linalg.lstsq(X, ds[ok], rcond=None)
        resid = ds[ok] - X @ beta
        rho_part = spearman(lg[ok], resid)
        print(f'\n=== [5] 偏 Mantel：控制地理距离后，语言距离 × |Δsat| 残差 ===')
        print(f'  ρ = {rho_part:+.4f}  (n={ok.sum()})')
    else:
        rho_part = None
        print(f'\n[partial] 语言成对过少 ({ok.sum()})，跳过')

    out = dict(countries=len(ctrys), pairs=int(valid.sum()),
               geo_mantel=dict(rho=round(rho1, 4), z=round(z1, 1), p=round(p1, 4)),
               geo_terciles=dict(t1=round(float(t1.mean()), 3), t2=round(float(t2.mean()), 3),
                                 t3=round(float(t3.mean()), 3),
                                 cut1=round(float(q1), 0), cut2=round(float(q2), 0)),
               binary_links=res_bin,
               partial_lang_after_geo=dict(rho=round(rho_part, 4)) if rho_part is not None else None)
    with open('probe10_results.json', 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'\n[done] {time.time()-t0:.1f}s -> probe10_results.json')

if __name__ == '__main__':
    main()
