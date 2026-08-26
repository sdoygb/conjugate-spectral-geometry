import urllib.request, re

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'replace')

src = fetch('https://raw.githubusercontent.com/cyanheads/imf-mcp-server/main/src/services/imf-sdmx/imf-sdmx-service.ts')
print('===== imf-sdmx-service.ts (%d chars) =====' % len(src))
# 打印所有 URL 构造和 fetch 调用
for m in re.finditer(r'[^\n]*(?:fetch|URL|/dataflow|/data/|external/sdmx|listDataflows|queryData|getDataflow)[^\n]*', src):
    line = m.group(0).strip()
    if line and len(line) < 300:
        print('  ', line[:260])
