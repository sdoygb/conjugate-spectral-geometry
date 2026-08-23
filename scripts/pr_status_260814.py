import json, os, ssl, urllib.request, sys

ROOT = os.path.expanduser("~/Downloads/GeometryAI-Mac-Build")
TOKEN = open(os.path.join(ROOT, ".github_token")).read().strip()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + TOKEN,
        "User-Agent": "qutip-berry-dev",
        "Accept": "application/vnd.github+json",
    })
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.load(r)

def show_pr(repo, num):
    pr = get(f"https://api.github.com/repos/{repo}/pulls/{num}")
    print(f"=== {repo} PR #{num} ===")
    print("state:", pr["state"], "| draft:", pr["draft"])
    print("title:", pr["title"])
    print("head:", pr["head"]["repo"]["full_name"], "branch:", pr["head"]["ref"], "sha:", pr["head"]["sha"][:8])
    print("base:", pr["base"]["ref"], pr["base"]["sha"][:8])
    try:
        st = get(f"https://api.github.com/repos/{repo}/commits/{pr['head']['sha']}/status")
        print("combined status:", st["state"], f"({st['total_count']} statuses)")
        for s in st["statuses"][:12]:
            print("   -", s["context"], "->", s["state"], str(s.get("description", ""))[:70])
    except Exception as e:
        print("status error:", e)
    try:
        cs = get(f"https://api.github.com/repos/{repo}/issues/{num}/comments")
        latest = f"{cs[-1]['user']['login']} {cs[-1]['created_at'][:10]}" if cs else "-"
        print("issue comments:", len(cs), "| latest:", latest)
    except Exception as e:
        print("comments error:", e)
    print()

for repo, num in [("qutip/qutip", 2974), ("geoopt/geoopt", 250)]:
    try:
        show_pr(repo, num)
    except Exception as e:
        print(f"{repo} #{num} ERROR: {e}\n")

# tqec PR detail (need head ref for local checkout)
try:
    pr = get("https://api.github.com/repos/tqec/tqec/pulls/1029")
    print("=== tqec/tqec PR #1029 ===")
    print("state:", pr["state"], "| draft:", pr["draft"])
    print("head:", pr["head"]["repo"]["full_name"], "branch:", pr["head"]["ref"], "sha:", pr["head"]["sha"][:8])
    print("base:", pr["base"]["ref"], pr["base"]["sha"][:8])
    cs = get("https://api.github.com/repos/tqec/tqec/issues/1029/comments")
    print("issue comments:", len(cs))
    for c in cs:
        print(f"  [{c['user']['login']} {c['created_at'][:10]}] {c['body'][:120]}")
except Exception as e:
    print("tqec #1029 ERROR:", e)
