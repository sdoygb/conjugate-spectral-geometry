import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

candidates = [
    # (名称, URL, headers)
    ('portal idata dataflow', 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF/DOT',
     {'Ocp-Apim-Subscription-Key': KEY}),
    ('portal idata qkey', 'https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF/DOT?subscription-key=' + KEY, {}),
    ('portal imf dataflow', 'https://portal.api.imf.org/imf/sdmx/3.0/dataflow/IMF/DOT?subscription-key=' + KEY, {}),
    ('api2.1 dataflow', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF/DOT', {}),
    ('api2.1 data DOT', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,./ALL?format=compact', {}),
    ('api3 dataflow DOT key', 'https://api.imf.org/external/sdmx/3.0/dataflow/IMF/DOT',
     {'Ocp-Apim-Subscription-Key': KEY}),
    ('portal idata data DOT', 'https://portal.api.imf.org/idata/sdmx/3.0/data/IMF,DOT,./ALL',
     {'Ocp-Apim-Subscription-Key': KEY}),
    ('dataservices json', 'https://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow/IMF', {}),
]

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type', ''), e.read()
    except Exception as e:
        return 'ERR', '', str(e).encode()

for name, url, hdrs in candidates:
    st, ct, body = fetch(url, hdrs)
    snippet = body[:120].decode('utf-8', 'replace').replace('\n', ' ')
    print(f'[{st}] {name}  ({ct})')
    print(f'    {snippet}')
