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

def fetch(path, show=5500):
    try:
        d = api(REPO + "/contents/" + path)
        txt = base64.b64decode(d["content"]).decode("utf-8", errors="replace")
        print(f"\n=== {path} ({len(txt)} chars) ===")
        print(txt[:show])
        if len(txt) > show:
            print(f"...[truncated, {len(txt)-show} more chars]")
    except Exception as e:
        print(f"\n{path}: ERROR {e}")

# 1. .github dir
try:
    gh = api(REPO + "/contents/.github")
    print("=== .github/ ===")
    for f in gh:
        print(f["type"], f["name"])
except Exception as e:
    print(".github error:", e)

# 2. develop-guide files
fetch("docs/sphinx/source/develop-guide/code-commit.rst")
fetch("docs/sphinx/source/develop-guide/develop-guide.rst", 3500)
fetch("docs/sphinx/source/develop-guide/run-test.rst", 2500)
fetch("docs/sphinx/source/develop-guide/develop-environment.rst", 2000)
