import json, ssl, os, urllib.request

TOKEN = open(os.path.expanduser('~/Downloads/GeometryAI-Mac-Build/.github_token')).read().strip()
ctx = ssl._create_unverified_context()
UA = {"User-Agent": "Mozilla/5.0", "Authorization": "Bearer " + TOKEN,
      "Accept": "application/vnd.github+json"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode())

def raw(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return r.read().decode()

repo = get("https://api.github.com/repos/pymanopt/pymanopt")
branch = repo["default_branch"]
print("default branch:", branch)
base = "https://raw.githubusercontent.com/pymanopt/pymanopt/%s" % branch

print("\n=== sphere.py ===")
print(raw(base + "/src/pymanopt/manifolds/sphere.py"))
