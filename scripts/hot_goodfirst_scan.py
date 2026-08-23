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


REPOS = [
    "PennyLaneAI/pennylane",
    "quantumlib/Cirq",
    "qutip/qutip",
    "Qiskit/qiskit",
]

for repo in REPOS:
    print("=" * 78)
    print(repo)
    seen = {}
    for label in ["good+first+issue", "help+wanted"]:
        try:
            items = api(
                f"/repos/{repo}/issues?labels={label}&state=open&per_page=50"
            )
        except Exception as e:
            print(f"  ! {label} failed: {e}")
            continue
        for i in items:
            if "pull_request" in i:
                continue
            n = i["number"]
            if n in seen:
                continue
            seen[n] = True
            assignee = i["assignee"]["login"] if i["assignee"] else "-"
            labels = ",".join(l["name"] for l in i["labels"])
            created = i["created_at"][:10]
            updated = i["updated_at"][:10]
            print(
                f"  #{n} [{labels}] assignee={assignee} "
                f"created={created} updated={updated} comments={i['comments']}"
            )
            print(f"      {i['title'][:110]}")
    print()
