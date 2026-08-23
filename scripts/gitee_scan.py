#!/usr/bin/env python3
"""Scan Gitee for active quantum-information repositories. Data as of run time."""
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def api(path, params=None):
    if params:
        path += "?" + urllib.parse.urlencode(params)
    try:
        return json.loads(get("https://gitee.com/api/v5" + path))
    except Exception as e:
        return {"__error__": f"{type(e).__name__}: {e}"}


def show_repo(d, brief=False):
    if not isinstance(d, dict) or "__error__" in d:
        print("    ERR:", d.get("__error__", d))
        return
    if brief:
        print(f"    {d.get('full_name')}: ★{d.get('stargazers_count')} "
              f"fork={d.get('forks_count')} upd={str(d.get('updated_at'))[:10]} "
              f"lang={d.get('language')} | {str(d.get('description'))[:60]}")
    else:
        print(f"  {d.get('full_name')}  ★{d.get('stargazers_count')}  "
              f"fork={d.get('forks_count')}  open_issues={d.get('open_issues_count')}  "
              f"updated={d.get('updated_at')}  lang={d.get('language')}")
        print(f"    desc: {d.get('description')}")


def main():
    print("=== 1. API anonymous smoke test ===")
    smoke = api("/repos/mindspore/mindquantum")
    print("  smoke keys:", list(smoke.keys())[:6] if isinstance(smoke, dict) else smoke)

    print("\n=== 2. known candidates ===")
    for full in ["mindspore/mindquantum", "OriginQ/QPanda-2",
                 "paddlepaddle/quantum", "PaddlePaddle/Quantum"]:
        o, r = full.split("/")
        show_repo(api(f"/repos/{o}/{r}"), brief=True)
        time.sleep(0.5)

    print("\n=== 3. org listings ===")
    for org in ["OpenWuYue", "quingo", "OriginQ"]:
        print(f"  -- org {org}:")
        data = api(f"/users/{org}/repos", {"per_page": 30})
        if isinstance(data, list):
            for d in data:
                show_repo(d, brief=True)
            if not data:
                print("    (empty)")
        else:
            show_repo(data)
        time.sleep(0.5)

    print("\n=== 4. Gitee search: q=量子计算, sort by stars ===")
    for q in ["量子计算", "quantum"]:
        data = api("/search/repositories", {"q": q, "per_page": 15,
                                            "sort": "stars_count", "order": "desc"})
        if isinstance(data, list):
            print(f"  -- q={q}: {len(data)} results")
            for d in data[:15]:
                show_repo(d, brief=True)
        else:
            show_repo(data)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
