#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知乎登录：保存 storage_state 供发布脚本复用
用法: python3 zhihu_login.py
首次运行会打开浏览器窗口，请用知乎 App 扫码登录。
登录成功后自动保存 zhihu_publish/storage_state.json。

v2: 改用 cookie(z_c0) 轮询检测登录，不强制导航，避免打断扫码流程。
"""
import os, time
from playwright.sync_api import sync_playwright

STATE_FILE = os.path.join(os.path.dirname(__file__), 'storage_state.json')
TIMEOUT = 900  # 15分钟


def has_zc0(ctx):
    for c in ctx.cookies():
        if c.get('name') == 'z_c0':
            return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            locale='zh-CN',
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/126.0.0.0 Safari/537.36',
        )
        page = ctx.new_page()
        page.goto('https://www.zhihu.com/signin', wait_until='domcontentloaded')
        print('=== 请在浏览器中扫码登录知乎（15分钟超时）===', flush=True)
        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            if has_zc0(ctx):
                break
            time.sleep(2)
        if not has_zc0(ctx):
            print('超时未登录', flush=True)
            browser.close()
            return 1
        time.sleep(2)  # 等 cookie 稳定
        ctx.storage_state(path=STATE_FILE)
        print('已保存登录状态:', STATE_FILE, flush=True)
        browser.close()
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
