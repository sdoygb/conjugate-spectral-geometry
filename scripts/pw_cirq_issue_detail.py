import json
import os
import ssl
import urllib.request

TOKEN = open(
    os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
).read().strip()
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "geometry-audit",
}
BASE = "https://api.github.com"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def api(path):
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
        return json.load(r)


def show(repo, number):
    try:
        i = api(f"/repos/{repo}/issues/{number}")
    except Exception as e:
        print(f"! {repo}#{number} issue failed: {e}")
        return
    print("=" * 78)
    print(f"ISSUE {repo}#{number}: {i['title']}")
    print(f"  state={i['state']} labels={[l['name'] for l in i['labels']]} "
          f"assignee={i['assignee']} created={i['created_at'][:10]} "
          f"updated={i['updated_at'][:10]} comments={i['comments']}")
    print(f"  author={i['user']['login']}")
    body = (i.get("body") or "").strip()
    print(f"  body ({len(body)} chars):")
    for line in body.splitlines()[:40]:
        print("    | " + line)
    if len(body.splitlines()) > 40:
        print(f"    ... ({len(body.splitlines()) - 40} more lines)")
    try:
        comments = api(f"/repos/{repo}/issues/{number}/comments")
    except Exception as e:
        print(f"  ! comments failed: {e}")
        return
    print(f"  COMMENTS ({len(comments)}):")
    for c in comments:
        author = c["user"]["login"]
        date = c["created_at"][:10]
        text = (c.get("body") or "").strip().replace("\n", " ")
        text = text[:300] + ("..." if len(text) > 300 else "")
        print(f"    [{date}] {author}: {text}")


show("PennyLaneAI/pennylane", 8152)
print()
show("quantumlib/Cirq", 6531)
