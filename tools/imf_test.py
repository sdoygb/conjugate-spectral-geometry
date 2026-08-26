import urllib.request, urllib.error

KEY = open('/Users/oygb/.imf_api_key').read().strip()

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 'ERR', str(e).encode()

st, body = fetch('https://portal.api.imf.org/idata/sdmx/3.0/dataflow/IMF',
                 {'Ocp-Apim-Subscription-Key': KEY})
print('portal+key:', st, 'size=', len(body))
print(body[:400].decode('utf-8', 'replace'))
print('---')
st2, body2 = fetch('https://api.imf.org/external/sdmx/3.0/dataflow/IMF')
print('api.imf.org free:', st2, 'size=', len(body2))
print(body2[:300].decode('utf-8', 'replace'))
