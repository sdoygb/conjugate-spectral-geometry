import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

candidates = [
    ('df IMF,DOT', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF,DOT', {}),
    ('df IMF,DOT,latest', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF,DOT,latest?references=all', {}),
    ('data 3seg ALL', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,latest/ALL?format=compact', {}),
    ('data 2seg ALL', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT/ALL?format=compact', {}),
    ('data dots M.US.CN.TM', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,latest/M.US.CN.TM?format=compact', {}),
    ('data dots M.US.CN.TM 3dot', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,./M.US.CN.TM?format=compact', {}),
    ('df IMF.DOT', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF.DOT', {}),
    ('data IMF.DOT M.US.CN.TM', 'https://api.imf.org/external/sdmx/2.1/data/IMF.DOT/M.US.CN.TM?format=compact', {}),
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
    snippet = body[:200].decode('utf-8', 'replace').replace('\n', ' ')
    print(f'[{st}] {name}  ({ct})  size={len(body)}')
    print(f'    {snippet}')
