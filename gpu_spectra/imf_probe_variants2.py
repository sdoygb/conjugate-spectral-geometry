#!/usr/bin/env python3
"""IMF 数据端点第二轮探测：2.1 / dataservices / 常见免key路径"""
import urllib.request, urllib.error, json

KEY = open('/Users/oygb/.imf_api_key').read().strip()

VARIANT = [
    ("dataservices dataflow", 'https://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/IMF', {}),
    ("dataservices DOT data", 'https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IMF/DOT?startPeriod=2023&endPeriod=2024', {}),
    ("api.imf sdmx2.1 dataflow", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF', {}),
    ("api.imf sdmx3.0 data DOT", 'https://api.imf.org/external/sdmx/3.0/data/IMF,DOT,1.0.....A....', {}),
    ("api.imf sdmx2.1 data DOT", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0.....A....', {}),
    ("api.imf external dataflow old", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all', {}),
    ("dataservices DOT compact full", 'https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IMF/DOT?key=0000', {}),
]

for name, url, hdr in VARIANT:
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            snippet = body[:150]
            print(f"[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B head={snippet!r}\n")
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {name}\n     {e.read()[:200]!r}\n")
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {name}\n     {e}\n")
