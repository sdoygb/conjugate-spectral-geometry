#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取 IMTS 数据流完整结构定义，解析维度顺序/代码，重试数据端点多种格式"""
import json, urllib.request, urllib.error

STRUCT_URL = 'https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF.STA/IMTS/1.0.0?references=all'

def fetch(url, accept):
    req = urllib.request.Request(url, headers={'Accept': accept, 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type', ''), e.read()
    except Exception as e:
        return 'ERR', '', str(e).encode()

# 1) 拉结构定义
st, ct, body = fetch(STRUCT_URL, 'application/vnd.sdmx.structure+json;version=2.0.0')
print(f'=== structure: HTTP {st} | {ct[:40]} | {len(body)} bytes')
if st != 200:
    st, ct, body = fetch(STRUCT_URL, 'application/json')
    print(f'=== retry json: HTTP {st} | {len(body)} bytes')
open('/tmp/imts_structure.json', 'wb').write(body)

# 2) 解析
d = json.loads(body)
dataflows = d.get('data', {}).get('dataflows', [])
print(f'dataflows: {len(dataflows)}')
for df in dataflows:
    print('  ', df.get('id'), df.get('agencyID'), df.get('version'),
          df.get('name', {}).get('en', '?') if isinstance(df.get('name'), dict) else df.get('name', '?'))

dsd_refs = []
for df in dataflows:
    if df.get('id') == 'IMTS':
        for s in df.get('structure', []):
            print(f'  IMTS -> DSD ref: {s!r}')
            if isinstance(s, str):
                dsd_refs.append(s)

# 3) 提取所有 DataStructure 定义
dsds = d.get('data', {}).get('dataStructures', [])
print(f'dataStructures: {len(dsds)}')
target = None
for ds in dsds:
    print(f'  DSD: {ds.get("agencyID")}/{ds.get("id")}/{ds.get("version")}')
    if ds.get('id') in ('ECOFIN_DSD', 'IMTS_DSD') or target is None:
        target = ds

if target:
    dims = []
    for dk in target.get('dataStructureComponents', {}).get('dimensions', []):
        cpt = dk.get('conceptIdentity', {}).get('id', '?')
        lvl = dk.get('localRepresentation', {})
        vals = ('enum', lvl.get('enumeration', {}).get('id', '?')) if 'enumeration' in lvl else ('direct', None)
        dims.append((cpt, vals))
    print(f'  维度序列: {[c[0] for c in dims]}')
    print(f'  维度引用: {dims}')

# 4) 枚举码表
codes = {}
for cl in d.get('data', {}).get('codelists', []):
    cid = cl.get('id', '?')
    items = [(it.get('id'), it.get('name', {}).get('en', '?')) for it in cl.get('items', [])]
    codes[cid] = items

for cid, items in codes.items():
    cid_l = cid.lower()
    if 'freq' in cid_l:
        print(f'\n  FREQ codelist {cid}: {[i[0] for i in items]}')
    if ('country' in cid_l or 'area' in cid_l or 'geo' in cid_l) and len(items) < 400:
        ids = [i[0] for i in items]
        print(f'  AREA codelist {cid}: {len(items)} items | CN={("CN" in ids)}, TW={("TW" in ids)}, US={("US" in ids)}, CHN={("CHN" in ids)}, TWN={("TWN" in ids)} | 前20: {ids[:20]}')
    if 'indic' in cid_l or 'measure' in cid_l:
        print(f'  INDICATOR codelist {cid}: {[i[0] for i in items][:40]}')
