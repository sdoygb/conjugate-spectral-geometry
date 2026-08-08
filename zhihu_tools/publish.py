# -*- coding: utf-8 -*-
"""
publish.py — Playwright 自动发布知乎文章（方案A：浏览器自动化）

用法:
  python3 zhihu_tools/publish.py login                      # 首次：扫码登录，保存 cookie
  python3 zhihu_tools/publish.py publish <html文件> [标题]  # 发布文章（默认用 html 内 <h1> 作标题）

说明:
  - cookie 保存于 zhihu_tools/cookies.json，失效时重跑 login
  - 发布前请先用 --dry-run 检查编辑器定位是否成功
  - 知乎无公开 API，此脚本模拟真人操作；请低频使用、自行评估账号风险
"""
import argparse
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES = os.path.join(BASE_DIR, "cookies.json")
WRITE_URL = "https://zhuanlan.zhihu.com/write"
LOGIN_URL = "https://www.zhihu.com/signin"


def _launch(headless=False):
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="zh-CN",
    )
    if os.path.exists(COOKIES):
        ctx.storage_state(path=COOKIES) if False else ctx.add_cookies(json.load(open(COOKIES)))
    return pw, browser, ctx


def _save_cookies(ctx):
    state = ctx.storage_state()
    with open(COOKIES, "w", encoding="utf-8") as f:
        json.dump(state["cookies"], f, ensure_ascii=False, indent=1)
    print(f"✅ cookie 已保存: {COOKIES}")


def login():
    """headful 打开登录页，等用户扫码，保存 cookie"""
    pw, browser, ctx = _launch(headless=False)
    page = ctx.new_page()
    page.goto(LOGIN_URL)
    print("请在打开的浏览器中扫码/登录知乎……（登录成功后本脚本自动保存 cookie）")
    # 等待登录成功：检测 URL 跳离 signin 或页面出现用户名
    for _ in range(120):  # 最多等 10 分钟
        url = page.url
        if "signin" not in url and "login" not in url:
            time.sleep(3)
            break
        # 页面顶栏出现"创作中心"入口即视为已登录
        if page.locator("text=创作中心").count() > 0:
            break
        time.sleep(5)
    _save_cookies(ctx)
    browser.close()
    pw.stop()
    print("✅ 登录态已保存")


def _paste_html(page, html):
    """把 HTML 富文本粘贴到当前聚焦的编辑器"""
    # 权限：允许剪贴板写入
    ctx = page.context
    try:
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://zhuanlan.zhihu.com")
    except Exception as e:
        print(f"  [提示] 剪贴板权限授予失败: {e}")
    # 通过 ClipboardItem 写入 text/html
    page.evaluate("""async (html) => {
        const blob = new Blob([html], {type: 'text/html'});
        const item = new ClipboardItem({'text/html': blob});
        await navigator.clipboard.write([item]);
    }""", html)
    page.keyboard.press("Control+v")
    time.sleep(3)


def find_editor(page):
    """探测知乎编辑器的 contenteditable 元素"""
    for sel in [
        ".DraftEditor-root [contenteditable=true]",
        "div[contenteditable=true]",
        "[data-contents='true']",
    ]:
        loc = page.locator(sel).first
        if loc.count() > 0 and loc.is_visible():
            return loc
    return None


def publish(html_path, title=None, dry_run=False):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    if title is None:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else os.path.basename(html_path)
    title = title.strip()

    pw, browser, ctx = _launch(headless=dry_run is False and False)  # 默认 headful（可见，便于排错）
    page = ctx.new_page()
    page.goto(WRITE_URL, wait_until="domcontentloaded")
    time.sleep(4)

    # 1. 标题
    title_sel = "textarea, input[placeholder*='标题'], .PublicDraftEditorPlaceholder-root"
    title_loc = page.locator("textarea").first if page.locator("textarea").count() else None
    if title_loc is None:
        for sel in ["input[placeholder*='标题']", "div[data-contents='true']"]:
            if page.locator(sel).count():
                title_loc = page.locator(sel).first
                break
    if title_loc:
        title_loc.click()
        page.keyboard.insert_text(title)
        time.sleep(1)
        print(f"标题已填入: {title[:40]}")
    else:
        print("⚠️ 未找到标题输入框（可能编辑器结构变化），请手动检查")

    # 2. 正文：聚焦编辑器后粘贴 HTML
    editor = find_editor(page)
    if editor is None:
        print("❌ 未找到正文编辑器，请检查页面结构")
        if dry_run:
            page.screenshot(path=os.path.join(BASE_DIR, "out", "debug_editor.png"))
        browser.close(); pw.stop()
        return 1
    editor.click()
    time.sleep(1)
    if not dry_run:
        _paste_html(page, html)
    else:
        print("(dry-run 跳过粘贴)")
    page.screenshot(path=os.path.join(BASE_DIR, "out", "pre_publish.png"))

    # 3. 发布
    if dry_run:
        print("✅ dry-run 完成：编辑器定位成功，未点击发布")
        browser.close(); pw.stop()
        return 0
    pub_btn = page.locator("button:has-text('发布')").last
    if pub_btn.count() == 0:
        print("❌ 未找到发布按钮")
        browser.close(); pw.stop()
        return 1
    pub_btn.click()
    time.sleep(4)
    # 可能弹"选择专栏/发布设置"对话框 → 点确认
    confirm = page.locator("button:has-text('发布文章'), button:has-text('确认发布')")
    if confirm.count() > 0:
        confirm.first.click()
        time.sleep(4)
    page.screenshot(path=os.path.join(BASE_DIR, "out", "after_publish.png"))
    print("✅ 已点击发布。请查看截图 after_publish.png 确认结果。")
    print(f"   当前 URL: {page.url}")
    browser.close()
    pw.stop()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["login", "publish"])
    ap.add_argument("html", nargs="?", help="知乎 HTML 文件")
    ap.add_argument("title", nargs="?", help="可选标题（默认取 html 内 h1）")
    ap.add_argument("--dry-run", action="store_true", help="只定位编辑器不发布")
    args = ap.parse_args()
    if args.mode == "login":
        login()
    else:
        if not args.html:
            sys.exit("publish 模式需要 html 文件参数")
        sys.exit(publish(args.html, args.title, dry_run=args.dry_run))


if __name__ == "__main__":
    import re
    main()
