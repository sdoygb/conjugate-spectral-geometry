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

def show(owner_repo, query="state=open", limit=50, tag=""):
    url = f"https://api.github.com/repos/{owner_repo}/issues?{query}&per_page={limit}"
    items = get(url)
    print(f"\n=== {owner_repo} [{tag}] ({len(items)} open items) ===")
    for it in items:
        if "pull_request" in it:
            continue
        labels = ",".join(l["name"] for l in it.get("labels", []))
        print(f"  #{it['number']} [{labels}] {it['title']}")

show("PythonOT/POT", tag="all open")
show("ott-jax/ott", tag="all open")
show("ott-jax/ott", "labels=good+first+issue&state=open", tag="good-first")
show("pymanopt/pymanopt", limit=60, tag="all open")
show("DedalusProject/dedalus", "labels=good+first+issue&state=open", tag="good-first")
r = get("https://api.github.com/rate_limit")
print("\nrate remaining:", r["resources"]["core"]["remaining"])
