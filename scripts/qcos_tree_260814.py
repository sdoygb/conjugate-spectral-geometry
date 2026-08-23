import json, ssl, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def api(path):
    return json.loads(get("https://gitee.com/api/v5" + path))

def ls(path):
    r = api("/repos/WUYUEQbit/qcos/contents/" + path)
    if isinstance(r, list):
        print(f"\n[{path}] dir, {len(r)} entries:")
        for f in r:
            print("  ", f.get("type"), f.get("name"))
        return r
    print(f"[{path}] is a file")
    return None

ls("docs")
ls("docs/sphinx")
ls("docs/sphinx/source")
