#!/usr/bin/env python3
"""IMF dataflow 目录正确格式探测"""
import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

VARIANT = [
    ("dataflow IMF/all json", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all', {'Accept': 'application/vnd.sdmx.structure+json;version=1.0'}),
    ("dataflow IMF/all json2", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all?references=all', {'Accept': 'application/vnd.sdmx.structure+json;version=1.0'}),
    ("dataflow all json", 'https://api.imf.org/external/sdmx/2.1/dataflow/all', {'Accept': 'application/vnd.sdmx.structure+json;version=1.0'}),
    ("dataflow IMF/all plain", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all', {}),
    ("dataflow IMF/all key+plain", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all', {'Ocp-Apim-Subscription-Key': KEY}),
    ("dataflow IMF detail", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/DOT/1.0', {'Accept': 'application/vnd.sdmx.structure+json;version=1.0'}),
    ("dataflow IMF/all xml", 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/all', {'Accept': 'application/vnd.sdmx.structure+xml;version=2.1'}),
]

for name, url, hdr in VARIANT:
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            ct = r.headers.get('Content-Type', '?')
            print(f"[OK] {name}\n     HTTP {r.status} CT={ct} {len(body)}B\n     head={body[:300]!r}\n")
            if len(body) > 300 and b'dataflows' in body[:2000]:
                open('/tmp/imf_dataflows.json', 'wb').write(body)
                print("     ^ saved to /tmp/imf_dataflows.json")
    except urllib.error.HTTPError as e:
        print(f"[HTTP {e.code}] {name}\n     {e.read()[:250]!r}\n")
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {name}\n     {e}\n")
