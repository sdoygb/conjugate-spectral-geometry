import json, ssl, os, urllib.request, base64

TOKEN = open(os.path.expanduser('~/Downloads/GeometryAI-Mac-Build/.github_token')).read().strip()
ctx = ssl._create_unverified_context()
UA = {"User-Agent": "Mozilla/5.0", "Authorization": "Bearer " + TOKEN,
      "Accept": "application/vnd.github+json"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read().decode())

print("=== ISSUE 273 ===")
iss = get("https://api.github.com/repos/pymanopt/pymanopt/issues/273")
print("title:", iss["title"])
print("state:", iss["state"], "| user:", iss["user"]["login"], "| created:", iss["created_at"])
print("labels:", [l["name"] for l in iss["labels"]])
print("comments:", iss["comments"])
print("assignees:", [a["login"] for a in iss["assignees"]])
print("--- BODY ---")
print(iss["body"][:2500])

print("\n=== COMMENTS ===")
for c in get("https://api.github.com/repos/pymanopt/pymanopt/issues/273/comments"):
    print("---", c["user"]["login"], c["created_at"], "---")
    print(c["body"][:1500])

print("\n=== SEARCH: PRs mentioning doubly stochastic/birkhoff ===")
for q in ["repo:pymanopt/pymanopt+type:pr+doubly+stochastic",
          "repo:pymanopt/pymanopt+type:pr+birkhoff",
          "repo:pymanopt/pymanopt+type:pr+manifold"]:
    try:
        r = get("https://api.github.com/search/issues?q=" + q + "&per_page=10")
        print(q, "-> total:", r["total_count"])
        for it in r["items"][:10]:
            print("   #%d %s [%s] %s" % (it["number"], it["state"], it["user"]["login"], it["title"]))
    except Exception as e:
        print(q, "ERR", e)

print("\n=== MANIFOLDS DIR ===")
for f in get("https://api.github.com/repos/pymanopt/pymanopt/contents/src/pymanopt/manifolds"):
    print(f["name"], f["size"])
