import json, os, ssl, urllib.request

TOKEN = open(os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")).read().strip()

def api(url, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=body, method=method or ("POST" if data else "GET"),
        headers={
            "Authorization": "Bearer " + TOKEN,
            "User-Agent": "qldpc-dev",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, context=ssl._create_unverified_context()) as r:
        return json.load(r)


MSG = """Fixed the lint failures from the previous CI run (all were introduced by this PR):

- ruff check: 4x W605 invalid escape sequences in the `QuantumReedMullerCode` docstring (`\\R` etc.) -> switched to a raw docstring
- ruff format: wrapped the `super().__init__(...)` call to fit line length + isort ordering of `__all__` (QuantumReedMullerCode before QuditCode)
- mypy was already green on the previous run ("no issues found in 80 source files")

The new CI run for daa9ac1 is sitting in `action_required` state (awaiting workflow approval for this new head commit). Could you approve it so the checks can run?"""

# edit the broken comment instead of posting a new one
r = api(
    "https://api.github.com/repos/qLDPCOrg/qLDPC/issues/comments/5289721803",
    data={"body": MSG},
    method="PATCH",
)
print("comment updated:", r["id"], r["updated_at"])
print("---")
print(r["body"][:200])
