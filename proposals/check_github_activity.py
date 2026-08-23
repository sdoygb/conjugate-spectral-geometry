#!/usr/bin/env python3
"""Query GitHub for all public activity of user sdoygb and response status."""
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
    """Follow pagination; unwraps 'items' for search endpoints."""
    items, page = [], 1
    while True:
        data = gh(f"{url}&page={page}&per_page=100" if "?" in url else f"{url}?page={page}&per_page=100")
        batch = data.get("items", data) if isinstance(data, dict) else data
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


print("=" * 70)
print("1) PRs authored by sdoygb")
print("=" * 70)
for pr in gh_all("https://api.github.com/search/issues?q=author%3Asdoygb+type%3Apr"):
    print(f"  [{pr['state']:>6}] {pr['repository_url'].split('/')[-2]}/{pr['repository_url'].split('/')[-1]} #{pr['number']}: {pr['title']}")
    print(f"          url: {pr['html_url']} | comments: {pr['comments']} | updated: {pr['updated_at']}")

print()
print("=" * 70)
print("2) Issues authored by sdoygb")
print("=" * 70)
for it in gh_all("https://api.github.com/search/issues?q=author%3Asdoygb+type%3Aissue"):
    print(f"  [{it['state']:>6}] {it['repository_url'].split('/')[-2]}/{it['repository_url'].split('/')[-1]} #{it['number']}: {it['title']}")
    print(f"          url: {it['html_url']} | comments: {it['comments']} | updated: {it['updated_at']}")

print()
print("=" * 70)
print("3) ECZoo PRs (all states, by head repo sdoygb)")
print("=" * 70)
for pr in gh_all("https://api.github.com/repos/errorcorrectionzoo/eczoo_data/pulls?state=all"):
    if "sdoygb" in (pr["head"]["repo"] or {}).get("full_name", ""):
        print(f"  PR #{pr['number']} [{pr['state']}]: {pr['title']}")
        print(f"     url: {pr['html_url']} | created: {pr['created_at']} | comments: {pr['comments']}")
        if pr.get("merged"):
            print(f"     MERGED at {pr['merged_at']}")

print()
print("=" * 70)
print("4) QuTiP issue #2972 status + comments")
print("=" * 70)
issue = gh("https://api.github.com/repos/qutip/qutip/issues/2972")
print(f"  state: {issue['state']} | comments: {issue['comments']} | updated: {issue['updated_at']}")
for c in gh_all("https://api.github.com/repos/qutip/qutip/issues/2972/comments"):
    print(f"  --- comment by {c['user']['login']} at {c['created_at']}:")
    print("     " + c["body"][:300].replace("\n", "\n     "))
