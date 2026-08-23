#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑪：跨波次时间锁定检验（WVS Wave 5/6/7）
三尺度统计刚性的"长时间"条款社会版：
  同一批国家跨 10-18 年（2005→2023），集体均值排序是否锁定？
  个体重采样免疫是否跨波成立？

变量对应（生活满意度 1-10）：
  WV5: V11（满意度）, V2=ISO数字代码
  WV6: V11（满意度）, B_COUNTRY_ALPHA=ISO3
  WV7: Q49（满意度）,  B_COUNTRY_ALPHA=ISO3
"""
import pandas as pd
import numpy as np
import json, time

# ISO 3166-1 numeric -> alpha-3（仅 WV5 出现的 58 国）
ISO_NUM = {
    20:'AND',32:'ARG',36:'AUS',76:'BRA',100:'BGR',124:'CAN',152:'CHL',156:'CHN',
    158:'TWN',170:'COL',196:'CYP',231:'ETH',246:'FIN',250:'FRA',268:'GEO',276:'DEU',
    288:'GHA',320:'GTM',344:'HKG',348:'HUN',356:'IND',360:'IDN',364:'IRN',368:'IRQ',
    380:'ITA',392:'JPN',400:'JOR',410:'KOR',458:'MMR',466:'MLI',484:'MEX',498:'MDA',
    504:'MAR',528:'NLD',554:'NZL',578:'NOR',604:'PER',616:'POL',642:'ROU',643:'RUS',
    646:'RWA',688:'SRB',704:'VNM',705:'SVN',710:'ZAF',724:'ESP',752:'SWE',756:'CHE',
    764:'THA',780:'TTO',792:'TUR',804:'UKR',818:'EGY',826:'GBR',840:'USA',854:'BFA',
    858:'URY',894:'ZMB',
}

def clean_sat(s):
    """满意度 1-10，负值/缺失置 NaN"""
    s = pd.to_numeric(s, errors='coerce')
    return s.where(s >= 1)

def load_wv5():
    df = pd.read_csv('WV5_Data_csv_v20180912.csv', sep=';',
                     usecols=['V2', 'V22'], encoding='utf-8-sig',
                     dtype={'V2': int, 'V22': float})
    df['iso3'] = df['V2'].map(ISO_NUM)
    df['sat'] = clean_sat(df['V22'])
    out = df[['iso3', 'sat']].dropna(subset=['iso3', 'sat'])
    return out, 'WV5(2005-2009)'

def load_wv6():
    df = pd.read_csv('WV6_Data_csv_v20201117.csv', sep=';',
                     usecols=['B_COUNTRY_ALPHA', 'V23'], encoding='utf-8-sig',
                     dtype={'B_COUNTRY_ALPHA': str, 'V23': float})
    df['iso3'] = df['B_COUNTRY_ALPHA'].str.strip().str.upper()
    df['sat'] = clean_sat(df['V23'])
    out = df[['iso3', 'sat']].dropna(subset=['iso3', 'sat'])
    return out, 'WV6(2010-2014)'

def load_wv7():
    df = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', sep=',',
                     usecols=['B_COUNTRY_ALPHA', 'Q49'], encoding='utf-8-sig',
                     dtype={'B_COUNTRY_ALPHA': str, 'Q49': float})
    df['iso3'] = df['B_COUNTRY_ALPHA'].str.strip().str.upper()
    df['sat'] = clean_sat(df['Q49'])
    out = df[['iso3', 'sat']].dropna(subset=['iso3', 'sat'])
    return out, 'WV7(2017-2023)'

def country_means(df):
    g = df.groupby('iso3')['sat'].agg(['mean', 'count'])
    return g

def spearman(a, b):
    a = pd.Series(a); b = pd.Series(b)
    ra = a.rank(); rb = b.rank()
    d = (ra - rb) ** 2
    n = len(a)
    return 1 - 6 * d.sum() / (n * (n ** 2 - 1))

def bootstrap_rank_stability(dfA, dfB, n_iter=200, seed=42):
    """对两波各自做个体重采样, 重算国家均值, 再算跨波 Spearman ρ 的分布"""
    rng = np.random.default_rng(seed)
    keys = sorted(set(dfA['iso3']) & set(dfB['iso3']))
    rowsA = {k: dfA.loc[dfA['iso3'] == k, 'sat'].values for k in keys}
    rowsB = {k: dfB.loc[dfB['iso3'] == k, 'sat'].values for k in keys}
    rhos = []
    for _ in range(n_iter):
        mA = {k: rng.choice(v, size=len(v), replace=True).mean() for k, v in rowsA.items()}
        mB = {k: rng.choice(v, size=len(v), replace=True).mean() for k, v in rowsB.items()}
        rhos.append(spearman([mA[k] for k in keys], [mB[k] for k in keys]))
    rhos = np.array(rhos)
    return rhos.mean(), rhos.min(), rhos.std()

def main():
    t0 = time.time()
    waves = {'wv5': load_wv5(), 'wv6': load_wv6(), 'wv7': load_wv7()}
    for name, (df, label) in waves.items():
        print(f'[load] {label}: n={len(df):,}  countries={df["iso3"].nunique()}')
    print()

    means = {name: country_means(df) for name, (df, _) in waves.items()}
    keys = sorted(set(means['wv5'].index) & set(means['wv6'].index) & set(means['wv7'].index))
    print(f'[∩] 三波共同国家: {len(keys)} 个')
    print()

    # 1) 排序稳定性（真实均值）
    pairs = [('wv5', 'wv6', 'WV5→WV6 (5-8年)'),
             ('wv6', 'wv7', 'WV6→WV7 (3-9年)'),
             ('wv5', 'wv7', 'WV5→WV7 (8-18年)')]
    print('=== [1] 跨波国家均值排序 ρ (Spearman) ===')
    res = {}
    for a, b, label in pairs:
        ma = {k: means[a].loc[k, 'mean'] for k in keys}
        mb = {k: means[b].loc[k, 'mean'] for k in keys}
        rho = spearman([ma[k] for k in keys], [mb[k] for k in keys])
        print(f'  {label}: ρ={rho:.4f}')
        res[label] = round(float(rho), 4)
    print()

    # 2) 均值幅度变化（漂移多少）
    print('=== [2] 国家均值变化（满意度 1-10）===')
    for k in keys:
        m5 = means['wv5'].loc[k, 'mean']; m6 = means['wv6'].loc[k, 'mean']; m7 = means['wv7'].loc[k, 'mean']
    d57 = {k: means['wv7'].loc[k, 'mean'] - means['wv5'].loc[k, 'mean'] for k in keys}
    ds = np.array(list(d57.values()))
    print(f'  Δ(WV7-WV5): mean={ds.mean():+.3f}  std={ds.std():.3f}  min={ds.min():+.3f}  max={ds.max():+.3f}')
    print()

    # 3) 个体重采样免疫（跨波 bootstrap ρ）
    print('=== [3] 跨波 bootstrap 排序稳定性（200 次个体重采样）===')
    boot = {}
    for a, b, label in pairs:
        m, mn, sd = bootstrap_rank_stability(waves[a][0], waves[b][0], n_iter=200)
        print(f'  {label}: ρ_mean={m:.4f}  ρ_min={mn:.4f}  ρ_std={sd:.4f}')
        boot[label] = dict(mean=round(float(m), 4), min=round(float(mn), 4), std=round(float(sd), 4))
    print()

    # 4) 判别对照：随机打乱国家标签的 ρ 分布（基准）
    print('=== [4] 对照：打乱 WV7 国家标签后与 WV5 的 ρ（应≈0）===')
    rng = np.random.default_rng(7)
    m5 = np.array([means['wv5'].loc[k, 'mean'] for k in keys])
    m7 = np.array([means['wv7'].loc[k, 'mean'] for k in keys])
    nulls = []
    for _ in range(200):
        perm = rng.permutation(len(keys))
        nulls.append(spearman(m5, m7[perm]))
    nulls = np.array(nulls)
    print(f'  零假设分布: mean={nulls.mean():.4f}  std={nulls.std():.4f}  |ρ|max={np.abs(nulls).max():.4f}')
    print(f'  真实 ρ={spearman(m5, m7):.4f} vs 零假设 std={nulls.std():.4f} → 比值={spearman(m5, m7)/nulls.std():.1f}σ')
    print()

    out = dict(common_countries=len(keys), spearman=res,
               delta_wv7_minus_wv5=dict(mean=float(ds.mean()), std=float(ds.std()),
                                        min=float(ds.min()), max=float(ds.max())),
               bootstrap=boot, null=dict(mean=float(nulls.mean()), std=float(nulls.std())))
    with open('probe11_results.json', 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'[done] {time.time()-t0:.1f}s  -> probe11_results.json')

if __name__ == '__main__':
    main()
