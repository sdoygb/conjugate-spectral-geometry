"""Third update of our own comment on pymanopt #273: honest transport statement."""
import json
import os
import ssl
import urllib.request

TOKEN_PATH = os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
TOKEN = open(TOKEN_PATH).read().strip()
CTX = ssl._create_unverified_context()

COMMENT_ID = 5290121552

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
new = ("- Parallel transport: the tangent spaces are base-point independent, "
       "so the identity map is a valid transporter; the isometric parallel "
       "transport requires solving the parallel transport ODE and is left "
       "out of the initial implementation")
assert old in body, "target line not found"
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
print("comment updated:", d.get("updated_at"))
