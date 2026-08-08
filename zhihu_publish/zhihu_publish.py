#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知乎发布 v3：导入文档(MD) → 填标题 → 发布
用法: python3 zhihu_publish.py <input.md> [--publish]
  --publish  实际发布（默认 dry-run：导入+填标题，不发布，停留90秒供检查）
依赖: 先运行 zhihu_login.py 生成 storage_state.json
"""
import os, sys, time, argparse
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, 'storage_state.json')
WRITE_URL = 'https://zhuanlan.zhihu.com/write'


def extract_title(md_path):
    with open(md_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
    return os.path.basename(md_path).replace('.md', '')


def publish(md_path, do_publish):
    title = extract_title(md_path)
    print('标题:', title)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
        page = ctx.new_page()
        page.goto(WRITE_URL, wait_until='domcontentloaded', timeout=60000)
        time.sleep(6)
        if '/signin' in page.url:
            print('!! 登录态失效，请先运行 zhihu_login.py')
            browser.close()
            return 1

        # 1. 点工具栏"导入"
        page.click('button:has-text("导入")')
        time.sleep(2)
        # 2. 切"导入文档"tab
        page.click('text=导入文档')
        time.sleep(1)
        # 3. 点击上传区，捕获文件选择器，上传 md
        with page.expect_file_chooser(timeout=10000) as fc_info:
            page.click('text=点击选择本地文档')
        fc = fc_info.value
        fc.set_files(os.path.abspath(md_path))
        print('[1] 已上传:', os.path.basename(md_path))

        # 4. 等待导入完成（轮询编辑器内容）
        ok = False
        for i in range(30):
            time.sleep(2)
            n = page.evaluate("""() => {
                const ed = document.querySelector('[contenteditable=true]');
                return ed ? ed.innerText.length : -1;
            }""")
            if n > 1000:
                ok = True
                print(f'[2] 导入完成: 编辑器 {n} 字符')
                break
        if not ok:
            print('!! 导入超时（30秒）')
            browser.close()
            return 2

        # 5. 填标题
        ta = page.locator('textarea.Input').first
        ta.fill(title)
        time.sleep(1)
        got = ta.input_value()
        print('[3] 标题验证:', 'OK' if got == title else 'FAIL: ' + repr(got[:30]))

        # 6. 人工检查 + 发布
        if do_publish:
            print('[4] 人工检查 10 秒后发布…')
            time.sleep(10)
            # 点发布（排除"发布设置"）
            page.click('button:has-text("发布"):not(:has-text("设置"))', timeout=15000)
            time.sleep(4)
            # 处理确认弹窗
            for sel in ['button:has-text("确认发布")',
                        'button:has-text("发布文章")',
                        '.Modal button:has-text("发布"):not(:has-text("设置"))']:
                try:
                    b = page.query_selector(sel)
                    if b and b.is_visible():
                        b.click()
                        print('[5] 确认弹窗:', sel)
                        time.sleep(4)
                        break
                except Exception:
                    pass
            time.sleep(8)
            print('[6] 最终URL:', page.url)
        else:
            print('[4] DRY-RUN: 停留 90 秒供检查（不发布）')
            time.sleep(90)
        browser.close()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('md', help='输入 md 文件')
    ap.add_argument('--publish', action='store_true', help='实际发布')
    args = ap.parse_args()
    if not os.path.exists(STATE_FILE):
        print('!! 未找到登录状态，请先运行: python3 zhihu_publish/zhihu_login.py')
        return 1
    return publish(args.md, args.publish)


if __name__ == '__main__':
    sys.exit(main())
