#!/usr/bin/env python3
"""Gitee scan round 3: org homepage HTML + explore page with full browser headers."""
import re
import ssl
import urllib.request

UA_FULL = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA_FULL,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://gitee.com/",
}
ctx = ssl._create_unverified_context()


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_repo_links(html):
    # org homepage repo cards: href="/org/repo" patterns within project list
    links = re.findall(r'href="/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)"', html)
    seen, out = [], []
    for l in links:
        parts = l.split("/")
        if len(parts) == 2 and l not in seen and not any(
                k in parts[1].lower() for k in ["login", "logout", "about", "features",
                                                "explore", "signup", "help", "privacy",
                                                "terms", "api", "news", "blog", "site"]):
            seen.append(l)
            out.append(l)
    return out


def main():
    for org in ["OpenWuYue", "quingo"]:
        print(f"=== {org} homepage ===")
        try:
            html = get(f"https://gitee.com/{org}")
            links = extract_repo_links(html)
            print("links found:", links[:20])
        except Exception as e:
            print("error:", type(e).__name__, e)

    print("\n=== explore/quantum order=starred ===")
    try:
        html = get("https://gitee.com/explore/quantum?order=starred")
        print("len:", len(html))
        m = re.findall(r'href="/([\w.\-]+/[\w.\-]+)"[^>]*>(?:\s*<[^>]+>)*\s*([^<]{3,60})', html)
        print("links:", m[:30])
    except Exception as e:
        print("error:", type(e).__name__, e)


if __name__ == "__main__":
    main()
