#!/usr/bin/env python3
"""Detail check: comments, reviews, labels for each of sdoygb's items."""
import json
import urllib.request
from pathlib import Path

TOKEN = Path(__file__).resolve().parents[1] / ".github_token"
token = TOKEN.read_text().strip() if TOKEN.exists() else ""


def gh(url):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "activity-check",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def gh_all(url):
    items, page = [], 1
    while True:
        data = gh(f"{url}&page={page}&per_page=100" if "?" in url else f"{url}?page={page}&per_page=100")
        batch = data.get("items", data) if isinstance(data, dict) else data
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


TARGETS = [
    ("tqec/tqec", 1029, "pr"),
    ("qLDPCOrg/qLDPC", 567, "pr"),
    ("qLDPCOrg/qLDPC", 568, "pr"),
    ("qLDPCOrg/qLDPC", 566, "issue"),
    ("geomstats/geomstats", 2124, "pr"),
    ("errorcorrectionzoo/eczoo_data", 381, "pr"),
    ("qutip/qutip", 2972, "issue"),
]

for repo, num, kind in TARGETS:
    print("=" * 72)
    print(f"{repo} #{num} ({kind})")
    print("=" * 72)
    item = gh(f"https://api.github.com/repos/{repo}/{'pulls' if kind == 'pr' else 'issues'}/{num}")
    print(f"  state={item['state']} draft={item.get('draft')} merged={item.get('merged')}")
    print(f"  labels: {[l['name'] for l in item.get('labels', [])]}")
    print(f"  updated: {item['updated_at']}")
    if kind == "pr":
        revs = gh_all(f"https://api.github.com/repos/{repo}/pulls/{num}/reviews")
        for r in revs:
            print(f"  REVIEW [{r['state']}] by {r['user']['login']} at {r['submitted_at']}:")
            if r.get("body"):
                print("     " + r["body"][:500].replace("\n", "\n     "))
        try:
            rrs = gh_all(f"https://api.github.com/repos/{repo}/pulls/{num}/requested_reviewers")
            if isinstance(rrs, dict):
                rrs = rrs.get("users", [])
            print(f"  requested reviewers: {[u['login'] for u in rrs]}")
        except Exception as e:
            print(f"  requested reviewers: (n/a: {e})")
        for rc in gh_all(f"https://api.github.com/repos/{repo}/pulls/{num}/comments"):
            print(f"  INLINE REVIEW COMMENT by {rc['user']['login']} at {rc['created_at']} (path={rc.get('path')}):")
            print("     " + rc["body"][:400].replace("\n", "\n     "))
    for c in gh_all(f"https://api.github.com/repos/{repo}/issues/{num}/comments"):
        print(f"  COMMENT by {c['user']['login']} [{c['author_association']}] at {c['created_at']}:")
        print("     " + c["body"][:600].replace("\n", "\n     "))
    print()
