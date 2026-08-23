#!/usr/bin/env python3
"""Check CI status for sdoygb's PRs and dump full bot review."""
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


for repo, num in [("tqec/tqec", 1029), ("qLDPCOrg/qLDPC", 567),
                  ("qLDPCOrg/qLDPC", 568), ("geomstats/geomstats", 2124),
                  ("errorcorrectionzoo/eczoo_data", 381)]:
    print("=" * 72)
    print(f"{repo} #{num} — CI checks (latest runs)")
    print("=" * 72)
    head_sha = gh(f"https://api.github.com/repos/{repo}/pulls/{num}")["head"]["sha"]
    runs = gh(f"https://api.github.com/repos/{repo}/commits/{head_sha}/check-runs")
    for c in runs.get("check_runs", []):
        print(f"  [{c['status']:>9}/{c['conclusion'] or '?':>8}] {c['name']}")

print()
print("=" * 72)
print("tqec #1029 — full Greptile inline comments")
print("=" * 72)
for rc in gh_all("https://api.github.com/repos/tqec/tqec/pulls/1029/comments"):
    print(f"--- {rc['path']} (line {rc.get('line') or rc.get('original_line')})")
    print(rc["body"][:1500])
    print()
