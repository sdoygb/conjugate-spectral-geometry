#!/usr/bin/env python3
"""IMF SDMX 2.1 数据端点：修正 key 格式"""
import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()
HDR_KEY = {'Ocp-Apim-Subscription-Key': KEY}
HDR_JSON = {'Accept': 'application/vnd.sdmx.data+json;version=1.0.0'}
HDR_BOTH = {'Ocp-Apim-Subscription-Key': KEY, 'Accept': 'application/vnd.sdmx.data+json;version=1.0.0'}

VARIANT = [
    ("2.1 dataflow with key+json", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF', HDR_BOTH),
    ("2.1 dataflow with key only", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF', HDR_KEY),
    ("2.1 data DOT v1.0 json key", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0?startPeriod=2023&endPeriod=2024', HDR_BOTH),
    ("2.1 data DOT json key q", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/.A.....?startPeriod=2023&endPeriod=2024', HDR_BOTH),
    ("2.1 data DOT plain json", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/.A.....?startPeriod=2023&endPeriod=2024', HDR_JSON),
    ("2.1 data DOT no key", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/.A.....?startPeriod=2023&endPeriod=2024', {}),
    ("2.1 data DOT query key", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/.A.....?startPeriod=2023&endPeriod=2024&subscription-key=' + KEY, {}),
    ("2.1 data DOTS", 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOTS,1.0?startPeriod=2023&endPeriod=2024', HDR_BOTH),
]

for name, url, hdr in VARIANT:
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            print(f"[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B head={body[:200]!r}\n")
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {name}\n     {e.read()[:250]!r}\n")
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {name}\n     {e}\n")
