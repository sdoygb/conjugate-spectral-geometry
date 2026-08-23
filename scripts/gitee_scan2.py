#!/usr/bin/env python3
"""Gitee scan round 2: orgs endpoint + explore/quantum HTML page."""
import json
import re
import ssl
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
ctx = ssl._create_unverified_context()


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def api(path):
    try:
        req = urllib.request.Request("https://gitee.com/api/v5" + path, headers=UA)
        with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"__error__": f"{type(e).__name__}: {e}"}


def main():
    print("=== orgs endpoint ===")
    for org in ["OpenWuYue", "quingo", "OriginQ", "mindspore"]:
        data = api(f"/orgs/{org}/repos?per_page=30")
        if isinstance(data, list):
            print(f"-- {org}: {len(data)} repos")
            for d in data:
                print(f"   {d.get('full_name')}: ★{d.get('stargazers_count')} "
                      f"upd={str(d.get('updated_at'))[:10]} | {str(d.get('description'))[:55]}")
        else:
            print(f"-- {org}: {data.get('__error__')}")
        time.sleep(0.4)

    print("\n=== explore/quantum?order=starred HTML ===")
    try:
        html = get("https://gitee.com/explore/quantum?order=starred")
        # repo links: /owner/repo inside explore items; stars in a data or class attr
        titles = re.findall(r'<a[^>]+href="/([\w\.\-]+/[\w\.\-]+)"[^>]*class="project-title"', html)
        stars = re.findall(r'<span[^>]*class="stars-count"[^>]*>([\d\.kK万]*)</span>', html)
        print("html len:", len(html), "| titles:", titles[:20], "| stars:", stars[:20])
        items = re.findall(
            r'<a[^>]+href="/([\w\.\-]+/[\w\.\-]+)"[^>]*class="project-title"[^>]*>(.*?)</a>.*?'
            r'class="stars-count"[^>]*>([^<]*)</span>',
            html, re.S)
        print("parsed items:", len(items))
        for path, t, s in items[:25]:
            print(f"  {path} ★{s}  {t.strip()[:50]}")
        if not items:
            # fallback: find section around 'quantum'
            m = re.search(r'project-title', html)
            print("has project-title:", bool(m))
            print(html[:2000])
    except Exception as e:
        print("explore error:", type(e).__name__, e)


if __name__ == "__main__":
    main()
