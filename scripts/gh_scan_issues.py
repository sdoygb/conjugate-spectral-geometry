#!/usr/bin/env python3
"""Good-first / help-wanted open issues for the hot & responsive candidates."""
import json
import os
import ssl
import urllib.request

TOKEN = open(
    os.path.expanduser("~/Downloads/GeometryAI-Mac-Build/.github_token")
).read().strip()
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
API = "https://api.github.com"


def req(url):
    r = urllib.request.Request(url)
    r.add_header("Authorization", f"token {TOKEN}")
    r.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(r, context=CTX) as resp:
        return json.loads(resp.read().decode())


for repo, labels in [
    ("Qiskit/qiskit", "good first issue"),
    ("PennyLaneAI/pennylane", "good first issue"),
    ("quantumlib/Cirq", "good first issue"),
    ("qutip/qutip", "good first issue"),
    ("google-deepmind/optax", "good first issue"),
]:
    url = f"{API}/repos/{repo}/issues?labels={urllib.request.quote(labels)}" \
          f"&state=open&per_page=15"
    try:
        items = req(url)
    except Exception as e:
        print(f"{repo}: ! {e}")
        continue
    print(f"\n== {repo} [{labels}] open={len(items)}")
    for it in items[:12]:
        if "pull_request" in it:
            continue
        print(f"  #{it['number']} {it['title'][:90]}")
