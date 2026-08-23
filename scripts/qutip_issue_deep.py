import json, os, ssl, urllib.request

TOKEN = open(os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")).read().strip()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(url):
    req = urllib.request.Request(url, headers={
        "Authorization": "token " + TOKEN,
        "Accept": "application/vnd.github+json",
        "User-Agent": "geo-audit",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())

def show(owner, repo, num):
    try:
        iss = api(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}")
        comments = api(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments")
        print("=" * 70)
        print(f"### {owner}/{repo} #{num}  [{iss['state']}]")
        print(f"title: {iss['title']}")
        print(f"by {iss['user']['login']}  created {iss['created_at']}  updated {iss['updated_at']}")
        print(f"assignee: {iss['assignee']['login'] if iss['assignee'] else 'NONE'}")
        print(f"labels: {[l['name'] for l in iss['labels']]}")
        print("--- BODY ---")
        print(iss["body"] or "(empty)")
        print(f"--- COMMENTS ({len(comments)}) ---")
        for c in comments:
            body = (c["body"] or "").replace("\r", "")
            print(f"\n[{c['user']['login']} @ {c['created_at']}]")
            print(body[:1500] + ("...[truncated]" if len(body) > 1500 else ""))
        print()
    except Exception as e:
        print(f"! {owner}/{repo}#{num} failed: {e}")

show("qutip", "qutip", 1537)
show("qutip", "qutip", 1873)
