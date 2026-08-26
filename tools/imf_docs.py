import urllib.request, urllib.error

urls = [
    ('IMF API 官方页', 'https://data.imf.org/en/Resource-Pages/IMF-API'),
    ('cyanheads README', 'https://raw.githubusercontent.com/cyanheads/imf-mcp-server/main/README.md'),
    ('sdmx1 sources', 'https://sdmx1.readthedocs.io/en/v2.22.0/sources.html'),
]

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 'ERR', str(e).encode()

for name, url in urls:
    st, body = fetch(url)
    text = body.decode('utf-8', 'replace')
    # 提取含 sdmx / api.imf / portal.api 的行片段
    import re
    hits = re.findall(r'[^\n]{0,80}(?:api\.imf\.org|sdmx|idata)[^\n]{0,120}', text, re.I)
    print(f'===== [{st}] {name}  ({len(text)} chars) =====')
    for h in hits[:25]:
        print('  ', h.strip()[:200])
    print()
