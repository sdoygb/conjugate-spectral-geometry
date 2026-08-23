import json, urllib.request, ssl

TOKEN = open('/Users/oygb/Downloads/GeometryAI-Mac-Build/.github_token').read().strip()
HDRS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "gh-probe"}

def gh(path):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HDRS)
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read().decode())

# 1. 仓库是否存在
for repo in ("nicholasjng/qLDPC", "vprusso/toqito", "geoopt/geoopt"):
    try:
        r = gh(f"/repos/{repo}")
        print(f"repo {repo}: OK star={r['stargazers_count']} pushed={r['pushed_at'][:10]}")
    except Exception as e:
        print(f"repo {repo}: {e}")

print()
# 2. 我们账号在这些仓库的所有 PR/issue
import urllib.parse
for repo in ("nicholasjng/qLDPC", "vprusso/toqito", "geoopt/geoopt"):
    q = urllib.parse.quote(f"author:sdoygb repo:{repo}")
    try:
        r = gh(f"/search/issues?q={q}&per_page=20")
        print(f"sdoygb in {repo}: total={r['total_count']}")
        for it in r.get("items", []):
            print(f"  #{it['number']} {'PR' if 'pull_request' in it else 'ISSUE'} state={it['state']} created={it['created_at'][:10]} title={it['title'][:70]!r}")
    except Exception as e:
        print(f"search {repo}: {e}")
    print()
