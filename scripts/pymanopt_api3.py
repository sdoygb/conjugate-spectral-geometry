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

base = "https://raw.githubusercontent.com/pymanopt/pymanopt/master"

print("=== positive.py ===")
print(raw(base + "/src/pymanopt/manifolds/positive.py"))

print("\n=== tests dir ===")
for f in get("https://api.github.com/repos/pymanopt/pymanopt/contents/tests"):
    print(f["name"])

print("\n=== open PR age analysis ===")
for n in [245, 275, 255, 298, 253]:
    try:
        pr = get("https://api.github.com/repos/pymanopt/pymanopt/pulls/%d" % n)
        print("#%d [%s] %s | by %s | created %s | updated %s | comments %d | review_comments %d" % (
            n, pr["state"], pr["title"][:60], pr["user"]["login"],
            pr["created_at"][:10], pr["updated_at"][:10],
            pr["comments"], pr["review_comments"]))
    except Exception as e:
        print(n, "ERR", e)
