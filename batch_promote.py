# -*- coding: utf-8 -*-
"""全量入库批量脚本：DIRECT_PROMOTE 模式，提交即入库（用户指令 2026-08-09）。
用法：python3 batch_promote.py [--limit N] [--dry-run]
断点续传：已完成编号记录在 /tmp/batch_done.txt，重复运行自动跳过。"""
import sys, os, re, json, time, subprocess
sys.path.insert(0, 'app')
from master_client import MasterClient

ARTICLES = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/articles'
DONE_FILE = '/tmp/batch_done.txt'
FAIL_FILE = '/tmp/batch_failed.txt'

c = MasterClient()

# ---- 1. 主库已有编号 ----
truth = c.fetch_truth(force=True) or []
existing = set()
for t in truth:
    name = t.get('formula_name', '')
    m = re.match(r'^(定理|命题|引理|推论|原理|公理|定义)\s*([0-9.]+[a-z]?)', name)
    if m:
        existing.add(m.group(2).strip('.'))
print(f'[主库已有 {len(existing)} 个编号]', file=sys.stderr)

# ---- 2. 读清单去重 ----
lines = [l.strip() for l in open('/tmp/theorem_list.txt') if l.strip()]
seen = {}
for l in lines:
    m = re.match(r'^(定理|命题|引理|推论|原理|公理|定义)\s*([0-9.]+[a-z]?)\s*（([^）]+)）', l)
    if not m:
        continue
    ftype, num, name = m.group(1), m.group(2), m.group(3)
    # 去名称后缀噪音（"——机制探讨"等）
    name = re.sub(r'——.*$', '', name).strip()
    if num not in seen:
        seen[num] = (ftype, name)
print(f'[清单去重后 {len(seen)} 个]', file=sys.stderr)

# ---- 3. 排除已入库 + 已处理 ----
done = set()
if os.path.exists(DONE_FILE):
    done = set(l.strip() for l in open(DONE_FILE) if l.strip())
todo = {k: v for k, v in seen.items() if k not in existing and k not in done}
print(f'[待提交 {len(todo)} 个]', file=sys.stderr)

if '--dry-run' in sys.argv:
    for k, v in list(todo.items())[:20]:
        print(f'  {k} {v[0]}（{v[1]}）', file=sys.stderr)
    sys.exit(0)

limit = None
if '--limit' in sys.argv:
    limit = int(sys.argv[sys.argv.index('--limit') + 1])
if '--all' in sys.argv:
    limit = None  # 全部
if limit:
    todo = dict(list(todo.items())[:limit])

# ---- 4. 定位与提取 ----
_cache = {}
def locate(num):
    if num in _cache:
        return _cache[num]
    try:
        r = subprocess.run(['grep', '-rl', num, ARTICLES], capture_output=True, text=True, timeout=15)
        files = [f for f in r.stdout.strip().split('\n') if f.endswith('.md')]
        _cache[num] = files
        return files
    except Exception:
        _cache[num] = []
        return []

def extract_content(num, ftype, name):
    files = locate(num)
    if not files:
        return ''
    fn = files[0]
    try:
        txt = open(fn, encoding='utf-8').read()
        # 优先：类型+编号+名称完整匹配
        pat = re.compile(r'(?:^|\*{1,2}|#+\s*)' + re.escape(ftype) + r'\s*' + re.escape(num) + r'\s*（[^）]{0,40}）', re.M)
        m = pat.search(txt)
        if not m:
            pat2 = re.compile(r'(?:^|\*{1,2}|#+\s*)' + re.escape(ftype) + r'\s*' + re.escape(num), re.M)
            m = pat2.search(txt)
        if m:
            start = m.end()
            seg = txt[start:start + 700]
            seg = re.sub(r'[#*`>|]', '', seg)
            seg = re.sub(r'\s+', ' ', seg).strip()
            return seg[:450]
        return ''
    except Exception:
        return ''

# ---- 5. 批量提交（6线程并行）----
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
_lock = threading.Lock()
results = {'promoted': 0, 'failed': 0, 'no_content': 0}
fail_log = []
_ilock = threading.Lock()
_counter = [0]

def work(item):
    num, (ftype, name) = item
    content = extract_content(num, ftype, name)
    if not content:
        with _lock:
            results['no_content'] += 1
            fail_log.append((num, name, 'no_content'))
        return f'[{num}] 无内容'
    fname = f'{ftype} {num}（{name}）'
    derivation = f'来源：主库全量入库（DIRECT_PROMOTE 模式，2026-08-09）。原文见文章库 {num}。'
    try:
        resp = c.submit_formula(
            formula_name=fname,
            formula_content=content,
            derivation_chain=derivation,
            topology_class='A0',
        )
        st = resp.get('status', '?')
        if st == 'promoted':
            with _lock:
                results['promoted'] += 1
                with open(DONE_FILE, 'a') as f:
                    f.write(num + '\n')
        else:
            with _lock:
                results['failed'] += 1
                fail_log.append((num, name, st))
        return f'[{num}] -> {st}'
    except Exception as e:
        with _lock:
            results['failed'] += 1
            fail_log.append((num, name, str(e)[:80]))
        return f'[{num}] EXC {str(e)[:80]}'

items = list(todo.items())
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(work, it) for it in items]
    for fu in as_completed(futs):
        with _ilock:
            _counter[0] += 1
            print(f'[{_counter[0]}/{len(items)}] {fu.result()}', file=sys.stderr)

with open(FAIL_FILE, 'a') as f:
    for item in fail_log:
        f.write('|'.join(str(x) for x in item) + '\n')

print(json.dumps({'本轮': results, '累计已入库': len(done) + results['promoted']}, ensure_ascii=False))
