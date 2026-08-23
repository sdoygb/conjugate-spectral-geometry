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

def show_comments(repo, num):
    try:
        cs = gh(f"/repos/{repo}/issues/{num}/comments")
    except Exception as e:
        print(f"  comments: FAIL {e}")
        return
    print(f"  comments({len(cs)}):")
    for c in cs:
        body = c["body"].replace("\n", " ")[:400]
        print(f"    [{c['created_at'][:10]}] {c['user']['login']}: {body}")

def show_reviews(repo, num):
    try:
        rs = gh(f"/repos/{repo}/pulls/{num}/reviews")
    except Exception as e:
        print(f"  reviews: FAIL {e}")
        return
    print(f"  reviews({len(rs)}):")
    for r in rs:
        print(f"    [{r['submitted_at'][:10]}] {r['user']['login']}: {r['state']}")

def entry(repo, num):
    print(f"== {repo} #{num}")
    p = None
    for kind in ("pulls", "issues"):
        try:
            p = gh(f"/repos/{repo}/{kind}/{num}")
            break
        except Exception:
            continue
    if p is None:
        print("  NOT FOUND")
        return
    print(f"  kind={'PR' if 'pull_request' in p else 'issue'} state={p['state']} title={p['title'][:80]!r} updated={p['updated_at'][:10]}")
    if 'pull_request' in p:
        print(f"  merged={p['merged']} mergeable={p.get('mergeable')} draft={p['draft']} head={p['head']['ref']} base={p['base']['ref']}")
        show_reviews(repo, num)
        try:
            crs = gh(f"/repos/{repo}/commits/{p['head']['sha']}/check-runs")
            print(f"  checks({len(crs.get('check_runs', []))}):")
            for c in crs.get("check_runs", []):
                print(f"    [{c['name']}] {c['status']}/{c.get('conclusion')} done={c.get('completed_at', '')[:10]}")
        except Exception as e:
            print(f"  checks: FAIL {e}")
    show_comments(repo, num)

entry("nicholasjng/qLDPC", 567)
entry("vprusso/toqito", 1936)
entry("geoopt/geoopt", 250)
