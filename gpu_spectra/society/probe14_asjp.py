#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针⑭：ASJP 语言距离 × 国家满意度差异
三尺度统计刚性"群尺度/耦合配置"条款的社会检验：
  语言 = 文化传播/互动的历史结构（探针⑨中唯一松动的粗粒度代理），
  语言距离 = 成对耦合强度的连续代理。
  若"锁位于成对耦合配置层"成立，则语言距离应预测满意度差异
  （语言越近 → 满意度越相似；语言越远 → 差异越大）。

数据：
  ASJP lists.txt（词表，40 核心词，ISO 639-3 码）
  WVS Wave 7 v6.0（Q49 生活满意度 1-10，66 国）

检验：
  [1] Mantel 型：D_lang 上三角 × |Δsat| 上三角的 Spearman ρ + 置换零假设
  [2] 三分位单调性：语言距离 tercile 内平均 |Δsat|
  [3] 语系内 vs 语系间：|Δsat| 对照（置换 t 检验）
"""
import pandas as pd
import numpy as np
import json, re, time
from collections import defaultdict

# ---------- 1. 解析 ASJP lists.txt ----------
def parse_asjp(path):
    """返回 {iso3: {item_num: transcription}}，transcription 取第一个变体"""
    langs = defaultdict(dict)
    cur_iso = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            # 记录头：LANGNAME{CLASSIFICATION}
            if re.match(r'^[A-Z][A-Z0-9_]*\{', line):
                cur_iso = None
                continue
            # 元数据行（含 ISO 码）——在读词条之前
            m = re.search(r'\s([a-z]{3})\s+([a-z]{3})\s*$', line)
            if m and cur_iso is None and '\t' not in line:
                # 元数据行两个码：第一个是旧书目码(如 arm)，第二个是 ISO 639-3(如 hye)
                cur_iso = m.group(2) if m.group(2) else m.group(1)
                continue
            # 词条行：<num> <gloss>\t<trans> //
            if cur_iso is not None and '\t' in line:
                parts = line.split('\t')
                if len(parts) == 2:
                    trans = parts[1].replace('//', '').strip()
                    if trans and trans != 'XXX':
                        num = parts[0].split()[0]
                        try:
                            langs[cur_iso][int(num)] = trans.split(',')[0].strip()
                        except (ValueError, IndexError):
                            pass
    return {k: dict(v) for k, v in langs.items()}

# ---------- 2. 国家 → 语言映射（WVS7 66 国，官方/主导语言 ISO 639-3） ----------
CTRY_LANG = {
    'AND':'cat','ARG':'spa','ARM':'hye','AUS':'eng','BGD':'ben','BOL':'spa','BRA':'por',
    'CAN':'eng','CHL':'spa','CHN':'cmn','COL':'spa','CYP':'ell','CZE':'ces','DEU':'deu',
    'ECU':'spa','EGY':'arb','ETH':'amh','GBR':'eng','GRC':'ell','GTM':'spa','HKG':'yue',
    'IDN':'ind','IND':'hin','IRN':'pes','IRQ':'arb','JOR':'arb','JPN':'jpn','KAZ':'kaz',
    'KEN':'swh','KGZ':'kir','KOR':'kor','LBN':'arb','LBY':'arb','MAC':'yue','MAR':'arb',
    'MDV':'div','MEX':'spa','MMR':'mya','MNG':'khk','MYS':'zsm','NGA':'eng','NIC':'spa',
    'NIR':'eng','NLD':'nld','NZL':'eng','PAK':'urd','PER':'spa','PHL':'tgl','PRI':'spa',
    'ROU':'ron','RUS':'rus','SGP':'eng','SRB':'hbs','SVK':'slk','THA':'tha','TJK':'tgk',
    'TUN':'arb','TUR':'tur','TWN':'cmn','UKR':'ukr','URY':'spa','USA':'eng','UZB':'uzn',
    'VEN':'spa','VNM':'vie','ZWE':'sna',
}

def levenshtein(a, b):
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return max(la, lb)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + (a[i-1] != b[j-1]))
        prev = cur
    return prev[lb]

def ldnd(langA, langB, min_shared=20):
    """ASJP 标准归一化 Levenshtein 距离：共享词条 LD/max(len) 的平均"""
    shared = [k for k in langA if k in langB]
    if len(shared) < min_shared:
        return None
    ds = []
    for k in shared:
        ta, tb = langA[k], langB[k]
        denom = max(len(ta), len(tb))
        if denom == 0:
            continue
        ds.append(levenshtein(ta, tb) / denom)
    if len(ds) < min_shared:
        return None
    return float(np.mean(ds))

def spearman(a, b):
    from scipy.stats import rankdata
    ra = rankdata(a); rb = rankdata(b)
    n = len(a)
    return float(1 - 6 * np.sum((ra - rb)**2) / (n * (n**2 - 1)))

def main():
    t0 = time.time()
    # ASJP
    langs = parse_asjp('lists.txt')
    print(f'[asjp] 语言数: {len(langs):,}')
    # WVS7 满意度均值
    wvs = pd.read_csv('WVS_Cross-National_Wave_7_csv_v6_0.csv', sep=',',
                      usecols=['B_COUNTRY_ALPHA', 'Q49'], encoding='utf-8-sig',
                      dtype={'B_COUNTRY_ALPHA': str, 'Q49': float})
    wvs['iso3'] = wvs['B_COUNTRY_ALPHA'].str.strip().str.upper()
    wvs['sat'] = pd.to_numeric(wvs['Q49'], errors='coerce').where(
        pd.to_numeric(wvs['Q49'], errors='coerce') >= 1)
    means = wvs.groupby('iso3')['sat'].mean()

    # 国家 → 语言词表
    ctrys = sorted([c for c in CTRY_LANG if c in means.index and CTRY_LANG[c] in langs])
    missing_lang = [c for c in CTRY_LANG if c in means.index and CTRY_LANG[c] not in langs]
    print(f'[map] 国家数: {len(ctrys)}（缺失语言条目: {missing_lang or "无"}）')
    print(f'[map] 语言去重后: {len(set(CTRY_LANG[c] for c in ctrys))} 种')

    # 成对距离矩阵
    n = len(ctrys)
    D_lang = np.full((n, n), np.nan)
    for i in range(n):
        for j in range(i + 1, n):
            d = ldnd(langs[CTRY_LANG[ctrys[i]]], langs[CTRY_LANG[ctrys[j]]])
            if d is not None:
                D_lang[i, j] = D_lang[j, i] = d
    sat = np.array([means[c] for c in ctrys])
    D_sat = np.abs(sat[:, None] - sat[None, :])

    idx = np.triu_indices(n, 1)
    dl = D_lang[idx]; ds = D_sat[idx]
    valid = ~np.isnan(dl)
    dl, ds = dl[valid], ds[valid]
    print(f'[pair] 有效成对: {len(dl)} / {len(idx[0])}')

    # [1] Mantel 型 Spearman + 置换零假设
    rho = spearman(dl, ds)
    rng = np.random.default_rng(42)
    nulls = []
    for _ in range(2000):
        perm = rng.permutation(n)
        ds_p = np.abs(sat[perm][:, None] - sat[perm][None, :])[idx][valid]
        nulls.append(spearman(dl, ds_p))
    nulls = np.array(nulls)
    z = (rho - nulls.mean()) / nulls.std()
    p = float((np.abs(nulls) >= abs(rho)).mean())
    print(f'\n=== [1] Mantel：语言距离 × |Δ满意度| ===')
    print(f'  ρ = {rho:+.4f}   置换零假设: mean={nulls.mean():+.4f} std={nulls.std():.4f}')
    print(f'  z = {z:+.1f}σ   p = {p:.4f}  (2000 置换)')

    # [2] 三分位单调性
    q1, q2 = np.quantile(dl, [1/3, 2/3])
    t1 = ds[dl <= q1]; t2 = ds[(dl > q1) & (dl <= q2)]; t3 = ds[dl > q2]
    print(f'\n=== [2] 语言距离三分位 → 平均 |Δ满意度| ===')
    print(f'  T1(近, d≤{q1:.3f}): mean={t1.mean():.3f}  n={len(t1)}')
    print(f'  T2(中):           mean={t2.mean():.3f}  n={len(t2)}')
    print(f'  T3(远, d>{q2:.3f}): mean={t3.mean():.3f}  n={len(t3)}')

    # [3] 语系内 vs 语系间（用 ASJP 分类粗分：同前 3 个字母的语系族名做不了，改用同语言/同语族近似）
    # 简化：同一种语言（距离=0）vs 不同语言
    same_lang = ds[dl == 0]; diff_lang = ds[dl > 0]
    print(f'\n=== [3] 同语言 vs 不同语言 ===')
    print(f'  同语言: mean={same_lang.mean():.3f}  n={len(same_lang)}')
    print(f'  不同:   mean={diff_lang.mean():.3f}  n={len(diff_lang)}')

    out = dict(countries=len(ctrys), pairs=len(dl),
               mantel=dict(rho=round(rho,4), null_mean=round(float(nulls.mean()),4),
                           null_std=round(float(nulls.std()),4), z=round(float(z),1), p=round(float(p),4)),
               terciles=dict(t1=round(float(t1.mean()),3), t2=round(float(t2.mean()),3),
                             t3=round(float(t3.mean()),3),
                             cut1=round(float(q1),3), cut2=round(float(q2),3)),
               same_vs_diff=dict(same=round(float(same_lang.mean()),3),
                                 diff=round(float(diff_lang.mean()),3)))
    with open('probe14_results.json', 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f'\n[done] {time.time()-t0:.1f}s -> probe14_results.json')

if __name__ == '__main__':
    main()
