#!/usr/bin/env python3
"""解析 IMTS dataflow 结构定义，提取真实维度编码
目标：确认 COUNTRY / INDICATOR / COUNTERPART_COUNTRY / FREQUENCY 的真实 code 列表
"""
import json, urllib.request, urllib.error

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            print(f"[OK] HTTP {r.status} {len(body)}B {url[:100]}")
            return body
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {url[:100]} :: {e.read()[:200]!r}")
        return None
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {url[:100]} :: {e}")
        return None

# IMTS 结构（上一轮已确认 200 + 2.9MB）
b = fetch('https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF.STA/IMTS/1.0.0?references=all',
          {'Accept': 'application/vnd.sdmx.structure+json;version=1.0.0'})
if not b:
    b = fetch('https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF.STA/IMTS/1.0.0?references=all')
if not b:
    raise SystemExit("结构下载失败")
open('/tmp/imf_imts_structure.json', 'wb').write(b)
print(f"saved /tmp/imf_imts_structure.json ({len(b)}B)")

d = json.loads(b)
data = d.get('data', {})
print("top keys:", list(d.keys()))
print("data keys:", list(data.keys()))

# 查找 dataflow 定义
flows = data.get('dataflows', [])
print(f"dataflows: {len(flows)}")
for f in flows:
    print("  flow:", f.get('id'), f.get('agencyID'), f.get('version'))
    # 找到结构引用
    sref = f.get('structure', {})
    print("    structure ref:", json.dumps(sref)[:300])

# 结构集
structs = data.get('structures', [])
print(f"structures: {len(structs)}")
for s in structs[:3]:
    print("  struct:", s.get('id'), s.get('agencyID'), s.get('version'), "type:", s.get('structureType'))
