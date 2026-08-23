import json, ssl, urllib.request, os
from datetime import datetime, timezone

TOKEN = open(os.path.expanduser('~/Downloads/GeometryAI-Mac-Build/.github_token')).read().strip()
ctx = ssl._create_unverified_context()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + TOKEN,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
        return json.loads(r.read().decode())

targets = [
    "graphnet-team/graphnet",
    "arguelles/nuSQuIDS",
    "nu-radio/NuRadioMC",
    "SNEWS2/snewpy",
    "icecube/pisa",
    "pyRiemann/pyRiemann",
    "pymanopt/pymanopt",
    "PythonOT/POT",
    "DedalusProject/dedalus",
    "ott-jax/ott",
    "yixuan/spectra",
]

for t in targets:
    print(f"\n===== {t} =====")
    # 1. 最近 30 个 merged PR 的作者分布
    try:
        prs = get(f"https://api.github.com/repos/{t}/pulls?state=closed&sort=updated&direction=desc&per_page=30")
        merged = [p for p in prs if p.get("merged_at")]
        authors = {}
        for p in merged:
            a = p["user"]["login"]
            authors[a] = authors.get(a, 0) + 1
        recent = sorted(authors.items(), key=lambda x: -x[1])[:8]
        print(f"  merged(30 most recent): {len(merged)}个, 作者数={len(authors)}")
        print(f"    分布: {recent}")
    except Exception as e:
        print("  PR err", e)
    # 2. good first issue
    try:
        gfi = get(f"https://api.github.com/search/issues?q=repo:{t}+is:issue+is:open+label:%22good+first+issue%22")
        hw = get(f"https://api.github.com/search/issues?q=repo:{t}+is:issue+is:open+label:%22help+wanted%22")
        print(f"  open issues: good-first={gfi['total_count']}, help-wanted={hw['total_count']}")
    except Exception as e:
        print("  issue err", e)
    # 3. CONTRIBUTING 存在性
    for br in ["master", "main"]:
        try:
            c = get(f"https://api.github.com/repos/{t}/contents/CONTRIBUTING.md?ref={br}")
            print(f"  CONTRIBUTING.md on {br}: YES ({c['size']} bytes)")
            break
        except Exception:
            continue
    else:
        print("  CONTRIBUTING.md: 未找到")
