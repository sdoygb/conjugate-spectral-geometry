import json, ssl, urllib.request, os

TOKEN = open(os.path.expanduser('~/Downloads/GeometryAI-Mac-Build/.github_token')).read().strip()
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "geometry-ai",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode())

def show(owner_repo, query, limit=30, tag=""):
    url = f"https://api.github.com/repos/{owner_repo}/issues?{query}&per_page={limit}"
    items = get(url)
    print(f"\n=== {owner_repo} [{tag}] ({len(items)} items) ===")
    for it in items:
        if "pull_request" in it:
            continue
        labels = ",".join(l["name"] for l in it.get("labels", []))
        body = (it.get("body") or "").replace("\n", " ")[:220]
        print(f"  #{it['number']} [{labels}] {it['title']}")
        print(f"      {body}")

# POT help-wanted + good-first
show("PythonOT/POT", "labels=help-wanted&state=open", tag="help-wanted")
show("PythonOT/POT", "labels=good+first+issue&state=open", tag="good-first")

# graphnet good-first + help-wanted
show("graphnet-team/graphnet", "labels=good+first+issue&state=open", tag="good-first")
show("graphnet-team/graphnet", "labels=help+wanted&state=open", tag="help-wanted")

# nuSQuIDS open issues
show("Arguelles/nuSQuIDS", "state=open", tag="open issues")

# rate limit check
r = get("https://api.github.com/rate_limit")
print("\nrate remaining:", r["resources"]["core"]["remaining"])
