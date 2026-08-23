import base64, json, ssl, urllib.request
from collections import Counter

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def api(path):
    return json.loads(get("https://gitee.com/api/v5" + path))

# 1. run-tests.rst
d = api("/repos/WUYUEQbit/qcos/contents/docs/sphinx/source/developer-guide/run-tests.rst")
txt = base64.b64decode(d["content"]).decode("utf-8", errors="replace")
print(f"=== run-tests.rst ({len(txt)} chars) ===")
print(txt[:4000])
if len(txt) > 4000:
    print(f"...[truncated {len(txt)-4000}]")

# 2. workflows
gh = api("/repos/WUYUEQbit/qcos/contents/.github/workflows")
print("\n=== .github/workflows ===")
for f in gh:
    print(" ", f.get("name"))

# 3. merged PR contributor distribution (external friendliness evidence)
print("\n=== recent 60 merged PRs by user ===")
users = Counter()
non_internal = []
page = 1
collected = 0
while collected < 60 and page <= 3:
    prs = api(f"/repos/WUYUEQbit/qcos/pulls?state=merged&per_page=20&page={page}&sort=created&direction=desc")
    if not prs:
        break
    for p in prs:
        users[p["user"]["login"]] += 1
        if p["user"]["login"] != "guo-zhufeng":
            non_internal.append((p["number"], p["user"]["login"], p["title"][:50], p["created_at"][:10]))
        collected += 1
    page += 1
print("user distribution:", dict(users))
print("\nnon-guozhufeng merged PRs:")
for row in non_internal:
    print("  #", row[0], row[1], "|", row[2], "|", row[3])
if not non_internal:
    print("  (none in the sample)")

# 4. open issues check
try:
    iss = api("/repos/WUYUEQbit/qcos/issues?state=open&per_page=5")
    print("\nopen issues:", len(iss))
    for i in iss:
        print("  #", i.get("number"), i.get("title", "")[:60], i.get("created_at", "")[:10])
except Exception as e:
    print("\nissues api:", e)
