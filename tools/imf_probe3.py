import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

candidates = [
    ('2.1 DOT v1.0 free', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/M.US.CN.TM?format=compact', {}),
    ('2.1 DOT v1.0 key', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/M.US.CN.TM?format=compact',
     {'Ocp-Apim-Subscription-Key': KEY}),
    ('2.1 IFS v1.0 free', 'https://api.imf.org/external/sdmx/2.1/data/IMF,IFS,1.0/M.US.PCPIPCH.PT?format=compact', {}),
    ('2.1 dataflow detail', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF?detail=all&format=compact', {}),
    ('2.1 DOT csv', 'https://api.imf.org/external/sdmx/2.1/data/IMF,DOT,1.0/M.US.CN.TM?format=csv', {}),
    ('idata 3.0 key', 'https://api.imf.org/idata/sdmx/3.0/dataflow/IMF/DOT',
     {'Ocp-Apim-Subscription-Key': KEY}),
    ('idata 3.0 free', 'https://api.imf.org/idata/sdmx/3.0/dataflow/IMF/DOT', {}),
    ('2.1 dataflow IMF.DOT v', 'https://api.imf.org/external/sdmx/2.1/dataflow/IMF,DOT,1.0', {}),
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
    snippet = body[:220].decode('utf-8', 'replace').replace('\n', ' ')
    print(f'[{st}] {name}  ({ct})  size={len(body)}')
    print(f'    {snippet}')
