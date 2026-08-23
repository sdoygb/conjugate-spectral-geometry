import base64, json, ssl, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def api(path):
    return json.loads(get("https://gitee.com/api/v5" + path))

REPO = "/repos/WUYUEQbit/qcos"

# 1. root listing
root = api(REPO + "/contents/")
print("=== ROOT FILES ===")
for f in root:
    print(f["type"], f["name"], f.get("size", ""))

# 2. look for .gitee dir
try:
    gitee_dir = api(REPO + "/contents/.gitee")
    print("\n=== .gitee/ ===")
    for f in gitee_dir:
        print(f["type"], f["name"])
except Exception as e:
    print("\n.gitee/ error:", e)

# 3. try to fetch CONTRIBUTING candidates
cands = ["CONTRIBUTING.md", "CONTRIBUTING_zh.md", "CONTRIBUTING_CN.md", "contributing.md"]
for c in cands:
    try:
        d = api(REPO + f"/contents/{c}")
        txt = base64.b64decode(d["content"]).decode("utf-8", errors="replace")
        print(f"\n=== {c} ({len(txt)} chars) ===")
        print(txt[:6000])
        break
    except Exception as e:
        print(f"\n{c}: not found ({e})")

# 4. recent PRs
print("\n=== RECENT 6 OPEN PRs ===")
prs = api(REPO + "/pulls?state=open&per_page=6")
for p in prs:
    print("---")
    print("#", p["number"], "|", p["title"], "|", p["created_at"], "| user:", p["user"]["login"])
    body = (p.get("body") or "")[:500].replace("\r", "")
    print("body:", body)
