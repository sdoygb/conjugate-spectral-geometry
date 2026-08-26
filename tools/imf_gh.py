import urllib.request, urllib.error, json, re

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 'ERR', str(e).encode()

# 1. 列目录
st, body = fetch('https://api.github.com/repos/cyanheads/imf-mcp-server/contents/src/services/imf-sdmx')
print('===== dir listing:', st, '=====')
if st == 200:
    items = json.loads(body)
    for it in items:
        print('  ', it['name'], it.get('download_url', ''))
else:
    print(body[:300])

# 2. 抓 README 中 base url 相关段落
st2, body2 = fetch('https://raw.githubusercontent.com/cyanheads/imf-mcp-server/main/README.md')
txt = body2.decode('utf-8', 'replace') if st2 == 200 else ''
for m in re.finditer(r'[^\n]{0,80}(?:IMF_BASE_URL|api\.imf\.org|/dataflow|/data/)[^\n]{0,140}', txt):
    print('  ~', m.group(0).strip()[:220])
