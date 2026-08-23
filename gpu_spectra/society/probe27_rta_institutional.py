#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探针㉗：制度流——全球贸易协定（RTA）网络的谱轨迹（1950-2024）
数据：WTO RTA-IS 全部通知协定（ExportAllRTAList，含 413 生效 + 213 历史失效）
方法：13 核心国（与 DOTS 货物流对齐）共同隶属生效 RTA → 0/1 边 → λ₂/BR 轨迹
"""
import openpyxl, numpy as np, json, re
from collections import defaultdict

# ---------- 13 核心国 ----------
CORE = ['CN', 'TW', 'US', 'JP', 'IN', 'DE', 'FR', 'IT', 'GB', 'CA', 'RU', 'KR', 'AU']
IDX = {c: i for i, c in enumerate(CORE)}

# ---------- 缔约方名 → ISO3 映射 ----------
NAME2ISO = {
    'United States': 'US', 'US': 'US', 'USA': 'US',
    'China': 'CN', "China, People's Republic of": 'CN', 'Chinese mainland': 'CN',
    'Chinese Taipei': 'TW', 'Taiwan': 'TW', 'Taiwan, Republic of China': 'TW',
    'Japan': 'JP', 'India': 'IN', 'Germany': 'DE', 'France': 'FR', 'Italy': 'IT',
    'United Kingdom': 'GB', 'UK': 'GB', 'Canada': 'CA', 'Russia': 'RU',
    'Russian Federation': 'RU', 'Korea, Republic of': 'KR', 'South Korea': 'KR',
    'Republic of Korea': 'KR', 'Korea': 'KR', 'Australia': 'AU',
    # EU members (27)
    'Austria': 'AT', 'Belgium': 'BE', 'Bulgaria': 'BG', 'Croatia': 'HR', 'Cyprus': 'CY',
    'Czech Republic': 'CZ', 'Denmark': 'DK', 'Estonia': 'EE', 'Finland': 'FI',
    'Greece': 'GR', 'Hungary': 'HU', 'Ireland': 'IE', 'Latvia': 'LV', 'Lithuania': 'LT',
    'Luxembourg': 'LU', 'Malta': 'MT', 'Netherlands': 'NL', 'Poland': 'PL',
    'Portugal': 'PT', 'Romania': 'RO', 'Slovak Republic': 'SK', 'Slovenia': 'SI',
    'Spain': 'ES', 'Sweden': 'SE',
}
EU27 = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT',
        'LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE']
# RTA 组织名 → 展开
ORG_EXPAND = {
    'European Union': EU27, 'EU': EU27, 'EC': EU27, 'European Community': EU27,
    'European Communities': EU27, 'EEC': EU27, 'European Free Trade Association': ['CH','NO','IS','LI'],
    'EFTA': ['CH','NO','IS','LI'], 'Pacific Alliance': ['MX','CO','PE','CL'],
}

def expand_parties(s):
    """把缔约方字符串展开为 ISO3 集合（含组织展开）；非核心国丢弃"""
    if not s: return set()
    out = set()
    for name in re.split(r'[;,]', s):
        name = name.strip()
        if not name: continue
        if name in ORG_EXPAND:
            out |= set(ORG_EXPAND[name]); continue
        # 组织名（含 'RTA'、'Union'、'Group'、'Association'、'Community'、'Cooperation' 等）跳过
        if re.search(r'RTA|Union|Group|Association|Community|Cooperation|Agreement|Initiative|Partnership|System|Area|Framework|Council|Scheme|Treaty|Organization|Organisation|Gulf|Andean|Mercosur|CARICOM|SADC|ASEAN|CIS|SAARC|ECOWAS|Pact', name):
            continue
        iso = NAME2ISO.get(name)
        if iso: out.add(iso)
    return out

# ---------- 读取 RTA ----------
wb = openpyxl.load_workbook('/tmp/wto_rta_all.xlsx', read_only=True, data_only=True)
ws = wb['AllRTAs']
rows = list(ws.iter_rows(values_only=True))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}

rtas = []
for r in rows[1:]:
    st = r[idx['Status']]
    if st not in ('In Force', 'In force for at least one Party', 'Inactive'):
        continue
    eif = r[idx['Date of Entry into Force (G)']]
    if not eif: continue
    year = int(eif.year)
    parties = expand_parties(r[idx['Original signatories']])
    if not parties: continue
    core_p = parties & set(CORE)
    if len(core_p) < 2: continue
    inactive = r[idx['Inactive Date']]
    end_year = int(inactive.year) if inactive else 9999
    rtas.append({'name': r[idx['RTA Name']], 'year': year, 'end': end_year,
                 'parties': core_p, 'status': st})
print(f"解析到 {len(rtas)} 个核心国相关 RTA（含历史失效）")

# 按生效年排序展示几个
rtas.sort(key=lambda x: x['year'])
print("最早 5 个：", [(t['year'], sorted(t['parties']), t['name'][:40]) for t in rtas[:5]])
print("最近 5 个：", [(t['year'], sorted(t['parties']), t['name'][:40]) for t in rtas[-5:]])

# ---------- 逐年构建网络 ----------
years = list(range(1950, 2025))
traj = []
for y in years:
    M = np.zeros((13, 13))
    for t in rtas:
        if t['year'] <= y < t['end']:
            ps = sorted(t['parties'])
            for i in range(len(ps)):
                for j in range(i+1, len(ps)):
                    a, b = IDX[ps[i]], IDX[ps[j]]
                    M[a, b] = M[b, a] = 1.0
    # λ₂ / BR（GCC 上，与探针㉕ 口径一致）
    deg = M.sum(axis=1)
    active = deg > 0
    n_act = int(active.sum())
    if n_act < 2:
        traj.append({'year': y, 'n_active': 0, 'lambda2': 0.0, 'BR': 0.0, 'edges': 0, 'gcc': 0}); continue
    # 最大连通分量
    import networkx as nx
    G = nx.from_numpy_array(M[active][:, active])
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    gcc_nodes = sorted(comps[0])
    n_gcc = len(gcc_nodes)
    Ms = M[active][:, active][np.ix_(gcc_nodes, gcc_nodes)]
    L = np.diag(Ms.sum(axis=1)) - Ms
    ev = np.sort(np.linalg.eigvalsh(L))
    l2 = float(ev[1]) if n_gcc > 1 else 0.0
    evA = np.sort(np.linalg.eigvalsh(Ms))
    n = len(evA)
    br = float(sum(abs(evA[i] + evA[n-1-i]) for i in range(n//2)) / (n//2)) if n > 1 else 0.0
    traj.append({'year': y, 'n_active': n_act, 'lambda2': l2, 'BR': br,
                 'edges': int(Ms.sum()/2), 'gcc': n_gcc})

# ---------- 输出 ----------
print("\n年  活跃 边数  λ₂       BR")
for t in traj:
    if t['year'] % 5 == 0 or t['year'] in (1950, 1955, 1990, 2000, 2010, 2024):
        print(f"{t['year']}  {t['n_active']:3d}  {t['edges']:3d}  {t['lambda2']:.4f}  {t['BR']:.4f}  GCC={t.get('gcc','-')}")

with open('gpu_spectra/society/rta_13_trajectory.csv', 'w') as f:
    f.write('year,n_active,edges,lambda2,BR,gcc\n')
    for t in traj:
        f.write(f"{t['year']},{t['n_active']},{t['edges']},{t['lambda2']:.6f},{t['BR']:.6f},{t.get('gcc',0)}\n")
print("\n已存 gpu_spectra/society/rta_13_trajectory.csv")
