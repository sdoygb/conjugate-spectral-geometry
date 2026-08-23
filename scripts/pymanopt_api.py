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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return r.read().decode()

print("=== sphere.py (implementation template) ===")
print(raw("https://raw.githubusercontent.com/pymanopt/pymanopt/main/src/pymanopt/manifolds/sphere.py"))

print("\n=== manifold.py abstract API (first 6000 chars) ===")
print(raw("https://raw.githubusercontent.com/pymanopt/pymanopt/main/src/pymanopt/manifolds/manifold.py")[:6000])
