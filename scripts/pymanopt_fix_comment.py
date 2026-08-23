"""Fix the parallel transport formula in our own comment on pymanopt #273."""
import json
import os
import ssl
import urllib.request

TOKEN_PATH = os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
TOKEN = open(TOKEN_PATH).read().strip()
CTX = ssl._create_unverified_context()

COMMENT_ID = 5290121552

# Get current body
req = urllib.request.Request(
    f"https://api.github.com/repos/pymanopt/pymanopt/issues/comments/{COMMENT_ID}",
    headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "sdoygb",
    },
)
with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
    body = json.loads(r.read().decode())["body"]

old = "- Parallel transport: P_{X -> Y}(V) = Pi_Y( V * Y / X )"
new = "- Parallel transport: P_{X -> Y}(V) = Pi_Y( V * sqrt(Y / X) )"
assert old in body, "target line not found in comment body"
body = body.replace(old, new)

req = urllib.request.Request(
    f"https://api.github.com/repos/pymanopt/pymanopt/issues/comments/{COMMENT_ID}",
    data=json.dumps({"body": body}).encode(),
    headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "sdoygb",
    },
    method="PATCH",
)
with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
    d = json.loads(r.read().decode())
print("updated:", d.get("updated_at"))
