#!/usr/bin/env python3
"""Publish the QuTiP Berry-toolbox feature request as a GitHub issue.

Token handling: reads the GitHub token from `.github_token` in the
project root. The token never appears on the command line, in the
conversation, or in git history (the file is git-ignored).

Usage:
    python3 proposals/publish_qutip_issue.py [owner repo]

The issue text is read from `proposals/qutip-berry-toolbox-issue.md`;
the metadata header and the internal-notes section are stripped, only
the body between "## Problem" and "## 内部备注" is published.
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUE_FILE = ROOT / "proposals" / "qutip-berry-toolbox-issue.md"
TOKEN_FILE = ROOT / ".github_token"

DEFAULT_OWNER = "qutip"
DEFAULT_REPO = "qutip"


def extract_title_and_body(text: str):
    """Split the draft into the issue title and the publishable body."""
    title = None
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if title is None:
        raise ValueError("draft has no '# Title' line")
    start = text.index("## Problem")
    end = text.index("## 内部备注")
    body = text[start:end].rstrip()
    if not body.strip():
        raise ValueError("draft body is empty")
    return title, body


def main() -> int:
    owner = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OWNER
    repo = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_REPO

    if not TOKEN_FILE.exists():
        print("错误：未找到 .github_token", file=sys.stderr)
        print(f"请在 {TOKEN_FILE} 中写入 GitHub token（仅 issues:write 权限即可）",
              file=sys.stderr)
        return 1
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        print("错误：.github_token 为空", file=sys.stderr)
        return 1

    text = ISSUE_FILE.read_text(encoding="utf-8")
    title, body = extract_title_and_body(text)

    payload = json.dumps({"title": title, "body": body}).encode("utf-8")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "qutip-geometry-proposal",
        },
    )
    print(f"发布到 {owner}/{repo} ...")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        print(f"发布失败：HTTP {exc.code}", file=sys.stderr)
        print(detail, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"网络错误：{exc.reason}", file=sys.stderr)
        return 1

    print(f"发布成功：{result['html_url']}")
    print(f"编号：#{result['number']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
