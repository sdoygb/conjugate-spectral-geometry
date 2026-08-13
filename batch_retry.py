# -*- coding: utf-8 -*-
"""补录脚本 v2：预加载文章到内存，按编号定位提取上下文，批量提交（DIRECT_PROMOTE）。"""
import sys, os, re, json, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/Users/oygb/Downloads/GeometryAI-Mac-Build/app')
from master_client import MasterClient

ARTICLES = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/articles'
DONE_FILE = '/tmp/retry_done.txt'
FAIL_FILE = '/tmp/retry_failed.txt'
LOCK = __import__('threading').Lock()

c = MasterClient()

# 预加载全部文章
ARTICLES_TEXT = {}
for fn in os.listdir(ARTICLES):
    if fn.endswith('.md'):
        try:
            with open(os.path.join(ARTICLES, fn), encoding='utf-8') as f:
                ARTICLES_TEXT[fn] = f.read()
        except Exception:
            pass
print(f'已加载 {len(ARTICLES_TEXT)} 篇文章', file=sys.stderr)

def extract_by_number(num, ftype):
    """按编号定位：优先找 '类型 编号' 定义模式，否则找编号首次出现处。"""
    for fn, txt in ARTICLES_TEXT.items():
        # 优先：类型 编号（定义模式）
        pat_def = re.compile(r'(' + re.escape(ftype) + r')\s*' + re.escape(num) + r'[^\n]{0,100}')
        m = pat_def.search(txt)
        if m:
            start = m.start()
            seg = txt[start:start + 800]
        else:
            idx = txt.find(num)
            if idx == -1:
                continue
            head = txt[max(0, idx - 150):idx]
            start = idx - len(head) + (head.rfind('\n') + 1)
            seg = txt[start:start + 800]
        seg = re.sub(r'[#*`>|]', '', seg)
        seg = re.sub(r'\s+', ' ', seg).strip()
        if len(seg) > 20:
            return seg[:500]
    return ''

def parse_failed(path):
    items = {}
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        parts = line.split('|')
        if len(parts) < 3:
            continue
        num, name, reason = parts[0], parts[1], parts[2]
        if reason in ('no_content', 'failed'):
            items.setdefault(num, (name, reason))
    return items

def submit_one(num, name, reason):
    content = extract_by_number(num, '命题')
    if not content:
        with LOCK:
            with open(FAIL_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{num}|{name}|still_no_content\n')
        return num, 'still_no_content'
    fname = f'命题 {num}（{name}）'
    derivation = f'来源：主库全量入库补录（DIRECT_PROMOTE）。编号 {num}，原文见文章库。'
    try:
        resp = c.submit_formula(
            formula_name=fname,
            formula_content=content,
            derivation_chain=derivation,
            topology_class='A0',
        )
        st = resp.get('status', '?')
        with LOCK:
            with open(DONE_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{num}|{name}|{st}\n')
        return num, st
    except Exception as e:
        with LOCK:
            with open(FAIL_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{num}|{name}|exc_{str(e)[:60]}\n')
        return num, 'exc'

def main():
    items = parse_failed('/tmp/batch_failed.txt')
    done = set()
    if os.path.exists(DONE_FILE):
        for line in open(DONE_FILE, encoding='utf-8'):
            parts = line.strip().split('|')
            if parts:
                done.add(parts[0])
    todo = {k: v for k, v in items.items() if k not in done}
    print(f'补录待提交: {len(todo)}', file=sys.stderr)
    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(submit_one, num, v[0], v[1]) for num, v in todo.items()]
        for i, fut in enumerate(futs):
            num, st = fut.result()
            results[st] = results.get(st, 0) + 1
            if (i + 1) % 20 == 0:
                print(f'[{i+1}/{len(todo)}] {num} -> {st}', file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False))

if __name__ == '__main__':
    main()
