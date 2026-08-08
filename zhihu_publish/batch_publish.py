#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知乎批量发布（手动发布模式，默认）：
  自动完成 导入MD → 填标题，然后【停下等你亲手点发布】；
  检测到发布成功后记录进度，等间隔，开下一篇。

用法:
  python3 batch_publish.py --preview              # 预览队列（不发布）
  python3 batch_publish.py --next                 # 发下一篇（默认手动发布）
  python3 batch_publish.py --run [--limit N]      # 连续队列（每篇都等你手动点发布）
  python3 batch_publish.py --next --auto          # 备用：全自动点发布（风险自担）
  python3 batch_publish.py --next --interval 30   # 间隔调成 30 分钟

进度记录在 published.log，可随时中断，重跑自动跳过已发布。
"""
import os, sys, time, re, glob, argparse, datetime
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # 项目根
ZH_DIR = os.path.join(ROOT, 'app/articles', 'ZH')
STATE_FILE = os.path.join(HERE, 'storage_state.json')
PUBLISHED_LOG = os.path.join(HERE, 'published.log')
ERROR_LOG = os.path.join(HERE, 'publish_errors.log')
WRITE_URL = 'https://zhuanlan.zhihu.com/write'
INTERVAL = 15 * 60                                # 默认间隔 15 分钟
MANUAL_TIMEOUT = 30 * 60                          # 等手动发布超时：30 分钟


def natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', name)]


def build_queue():
    files = [os.path.basename(f) for f in glob.glob(os.path.join(ZH_DIR, '*.md'))]
    files = [f for f in files if re.match(r'^\d+\.\d+', f)]   # 编号文章
    files.sort(key=natural_key)
    done = set()
    if os.path.exists(PUBLISHED_LOG):
        for line in open(PUBLISHED_LOG, encoding='utf-8'):
            if '|' in line:
                done.add(line.split('|')[1].strip())
    return [f for f in files if f not in done]


def extract_title(md_path):
    with open(md_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
    return os.path.basename(md_path).replace('.md', '')


def prepare_editor(page, md_path):
    """导入MD + 填标题。成功返回标题，失败返回 None。"""
    page.goto(WRITE_URL, wait_until='domcontentloaded', timeout=60000)
    time.sleep(6)
    if '/signin' in page.url:
        print('!! 登录态失效', flush=True)
        return None
    page.click('button:has-text("导入")')
    time.sleep(2)
    page.click('text=导入文档')
    time.sleep(1)
    with page.expect_file_chooser() as fc_info:
        page.click('text=点击选择本地文档')
    fc_info.value.set_files(os.path.abspath(md_path))
    ok = False
    for _ in range(30):
        time.sleep(2)
        n = page.evaluate("() => { const ed = document.querySelector('[contenteditable=true]'); return ed ? ed.innerText.length : -1; }")
        if n > 1000:
            ok = True
            break
    if not ok:
        print('!! 导入超时', flush=True)
        return None
    title = extract_title(md_path)
    ta = page.locator('textarea.Input').first
    ta.fill(title)
    return title


def publish_one(md_path, manual=True, interval=INTERVAL):
    """发布单篇。manual=True：等用户手动点发布；False：自动点。
    返回 (url, paused)：url 成功为文章URL，失败 None；paused 表示超时暂停需人工接手。"""
    title = extract_title(md_path)
    print(f'[{time.strftime("%H:%M:%S")}] 准备发布: {title}', flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state=STATE_FILE, locale='zh-CN')
        page = ctx.new_page()
        t = prepare_editor(page, md_path)
        if t is None:
            browser.close()
            return None, False
        time.sleep(8)   # 导入+标题完成后的人工检查窗口

        if manual:
            print('=' * 60, flush=True)
            print(f'[手动] 请在浏览器窗口检查内容，然后【亲手点击"发布"按钮】', flush=True)
            print(f'[手动] 脚本等待发布成功（最长 {MANUAL_TIMEOUT//60} 分钟），检测到后自动记录并继续', flush=True)
            print('=' * 60, flush=True)
            deadline = time.time() + MANUAL_TIMEOUT
            url = None
            while time.time() < deadline:
                time.sleep(3)
                cur = page.url
                if re.search(r'zhuanlan\.zhihu\.com/p/\d+', cur):
                    url = cur
                    break
            if url is None:
                print('!! 等待手动发布超时——队列暂停，等你处理后再续', flush=True)
                browser.close()
                return None, True
            browser.close()
            return url, False

        # ---- 自动模式（备用） ----
        page.click('button:has-text("发布"):not(:has-text("设置"))')
        time.sleep(4)
        for sel in ['button:has-text("确认发布")',
                    'button:has-text("发布文章")',
                    '.Modal button:has-text("发布"):not(:has-text("设置"))']:
            try:
                b = page.query_selector(sel)
                if b and b.is_visible():
                    b.click()
                    print('  确认弹窗:', sel, flush=True)
                    time.sleep(4)
                    break
            except Exception:
                pass
        time.sleep(6)
        url = page.url
        browser.close()
        if re.match(r'https://zhuanlan\.zhihu\.com/p/\d+', url):
            return url, False
        print('!! 发布后URL异常:', url, flush=True)
        return None, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--next', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--auto', action='store_true', help='自动点发布（不推荐）')
    ap.add_argument('--interval', type=int, default=INTERVAL // 60, help='篇间间隔（分钟）')
    args = ap.parse_args()

    interval = args.interval * 60
    queue = build_queue()
    if args.preview or not (args.run or args.next):
        mode = '自动' if args.auto else '手动（你点发布）'
        print(f'队列：共 {len(queue)} 篇（已排除 published.log 中的），间隔 {interval//60} 分钟/篇，发布方式: {mode}')
        for f in queue[:40]:
            print('  ', f)
        if len(queue) > 40:
            print(f'  ... 共 {len(queue)} 篇')
        return

    if not os.path.exists(STATE_FILE):
        print('!! 未找到登录状态，先运行 zhihu_login.py')
        return

    count = 0
    for f in queue:
        if args.limit and count >= args.limit:
            break
        md = os.path.join(ZH_DIR, f)
        url, paused = publish_one(md, manual=not args.auto, interval=interval)
        if url:
            with open(PUBLISHED_LOG, 'a', encoding='utf-8') as log:
                log.write(f'{datetime.datetime.now().isoformat()} | {f} | {url}\n')
            print(f'✓ 已发布: {url}', flush=True)
        else:
            with open(ERROR_LOG, 'a', encoding='utf-8') as log:
                log.write(f'{datetime.datetime.now().isoformat()} | {f} | 失败\n')
            print(f'✗ 失败/未发布: {f}（记录到 publish_errors.log）', flush=True)
        count += 1
        if paused:
            print('队列已暂停（等待手动发布超时），续跑: python3 zhihu_publish/batch_publish.py --run', flush=True)
            break
        if args.next:
            break
        remaining = (args.limit - count) if args.limit else None
        if remaining == 0 or f == queue[-1]:
            break
        print(f'-- 等待 {interval//60} 分钟 --', flush=True)
        time.sleep(interval)
    print('队列结束')


if __name__ == '__main__':
    main()
