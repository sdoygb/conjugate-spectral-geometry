import base64, json, ssl, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return r.read().decode("utf-8", errors="replace")

def api(path):
    return json.loads(get("https://gitee.com/api/v5" + path))

r = api("/repos/WUYUEQbit/qcos/contents/docs/sphinx/source/developer-guide")
print("=== developer-guide ===")
for f in r:
    print(" ", f.get("type"), f.get("name"), f.get("size"))

for f in r:
    if f.get("type") != "file":
        continue
    name = f.get("name")
    d = api("/repos/WUYUEQbit/qcos/contents/docs/sphinx/source/developer-guide/" + name)
    if not isinstance(d, dict):
        print(f"\n{name}: unexpected type {type(d)}")
        continue
    txt = base64.b64decode(d["content"]).decode("utf-8", errors="replace")
    print(f"\n=== {name} ({len(txt)} chars) ===")
    print(txt[:5500])
    if len(txt) > 5500:
        print(f"...[truncated {len(txt)-5500}]")
