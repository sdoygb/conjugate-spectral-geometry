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

# qLDPC 去向：nicholasjng 的仓库列表
try:
    rs = gh("/users/nicholasjng/repos?per_page=100&sort=updated")
    print(f"nicholasjng repos({len(rs)}):")
    for r in rs:
        print(f"  {r['full_name']} star={r['stargazers_count']} pushed={r['pushed_at'][:10]}")
except Exception as e:
    print(f"user repos: {e}")

print()
# 搜全局 qLDPC（可能改名/转移）
import urllib.parse
q = urllib.parse.quote("qLDPC in:name,description language:python")
try:
    r = gh(f"/search/repositories?q={q}&sort=stars&per_page=10")
    print(f"search qLDPC repos: total={r['total_count']}")
    for it in r.get("items", []):
        print(f"  {it['full_name']} star={it['stargazers_count']} pushed={it['pushed_at'][:10]}")
except Exception as e:
    print(f"search repos: {e}")

print()
# 两个 PR 的 reviews
for repo, num in (("vprusso/toqito", 1936), ("geoopt/geoopt", 250)):
    try:
        rs = gh(f"/repos/{repo}/pulls/{num}/reviews")
        print(f"{repo} #{num} reviews({len(rs)}):")
        for r in rs:
            print(f"  [{r['submitted_at'][:16]}] {r['user']['login']}: {r['state']}")
    except Exception as e:
        print(f"{repo} #{num} reviews: {e}")
