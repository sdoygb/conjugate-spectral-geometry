import json, ssl, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def api(path):
    return json.loads(get("https://gitee.com/api/v5" + path))

# default branch
repo = api("/repos/WUYUEQbit/qcos")
branch = repo.get("default_branch", "master")
print("default branch:", branch)

# try raw for each file
files = [
    "docs/sphinx/source/develop-guide/code-commit.rst",
    "docs/sphinx/source/develop-guide/develop-guide.rst",
    "docs/sphinx/source/develop-guide/run-test.rst",
    "docs/sphinx/source/develop-guide/develop-environment.rst",
]
for f in files:
    url = f"https://gitee.com/WUYUEQbit/qcos/raw/{branch}/{f}"
    try:
        txt = get(url)
        print(f"\n=== {f} ({len(txt)} chars) ===")
        print(txt[:6000])
    except Exception as e:
        print(f"\n{f}: ERROR {e}")
