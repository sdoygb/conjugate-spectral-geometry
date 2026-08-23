#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用图构建工具：扫描文章库，提取文章间引用关系，构建有向图。

用法:
  python3 tools/build_citation_graph.py                 # 构建 citation_graph.json + 统计
  python3 tools/build_citation_graph.py --out 2.6       # 2.6 引用了谁（出边）
  python3 tools/build_citation_graph.py --in 1.5        # 谁引用了 1.5（入边）
  python3 tools/build_citation_graph.py --path 2.6 1.5  # 2.6 到 1.5 的路径（BFS）
"""
import os, re, json, glob, sys
from collections import defaultdict, Counter

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(TOOLS_DIR, '..', 'app', 'articles')
OUT_JSON = os.path.join(TOOLS_DIR, 'citation_graph.json')

# ---------- 1. 收集文章编号 ----------
files = sorted(glob.glob(os.path.join(ARTICLES_DIR, '*.md')))
article_ids, id_to_file = set(), {}
for f in files:
    base = os.path.basename(f)
    m = re.match(r'^(\d{1,2})\.(\d{1,2})', base)
    if m:
        aid = f"{m.group(1)}.{m.group(2)}"
        article_ids.add(aid)
        id_to_file[aid] = f

# ---------- 2. 引用提取 ----------
pat_xyz = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})\.(\d{1,2})(?![0-9.])')  # X.Y.Z（定理/引理编号）
pat_xy  = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])')               # X.Y（文章编号）

W3_WORDS = ['文章', '详见', '参见', '参考', '见', '引用', '综述', '依赖']
W2_AFTER = ['§', '附录', '章', '节', '定理', '引理', '命题', '推论', '注', '公理']
W2_BEFORE = ['定理', '引理', '命题', '推论', '公理', '见', '参考', '详见']

def strip_math(text):
    """移除 LaTeX 公式（$...$、\(...\)、\[...\]），避免公式内数字误报。"""
    text = re.sub(r'\$[^$]*\$', ' ', text)
    text = re.sub(r'\\\(.*?\\\)', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', ' ', text, flags=re.DOTALL)
    return text

def strip_toc(text):
    """移除目录区块（## 目\u3000录 ... 到下一个 ## 或 ---），避免章节编号误判为文章引用。"""
    return re.sub(r'##\s*目\s*录.*?(?=\n##|\n---|\Z)', '', text, flags=re.DOTALL)

def weight_of(text, start, end):
    """根据上下文给引用定权重：3=显式文章引用 2=章节/定理级引用 1=括号引用 0=裸编号。"""
    before = text[max(0, start - 20):start]
    after = text[end:end + 20]
    for w in W3_WORDS:
        if w in before:
            return 3
    for w in W2_BEFORE:
        if w in before:
            return 2
    for w in W2_AFTER:
        if w in after:
            return 2
    # 括号内引用：（X.Y）
    if start > 0 and text[start - 1] in '（(':
        return 1
    return 0

graph = defaultdict(Counter)   # src -> {dst: count}
weights = defaultdict(int)  # (src,dst) -> max_weight
examples = defaultdict(list)   # (src,dst) -> [example contexts]

for aid, f in id_to_file.items():
    raw = open(f, encoding='utf-8').read()
    text = strip_toc(strip_math(raw))
    consumed = set()
    # 先找 X.Y.Z（定理级），归到 X.Y 文章级
    for m in pat_xyz.finditer(text):
        x, y, z = m.group(1), m.group(2), m.group(3)
        ref_xy = f"{x}.{y}"
        if ref_xy == aid or ref_xy not in article_ids:
            continue
        if m.end() < len(text) and text[m.end()] == '\u3000':
            continue  # 全角空格 = 目录/标题行，非引用
        if m.start() > 0 and text[m.start() - 1] in '§#':
            continue  # §X.Y = 本文内部章节引用
        if m.end() < len(text) and text[m.end()] == '%':
            continue  # 百分比数据
        if m.start() > 0 and text[m.start() - 1] in '-−':
            continue  # 负号（表格/公式）
        line_start = text.rfind('\n', 0, m.start()) + 1
        if text[line_start:m.start()].strip().startswith('#'):
            continue  # Markdown 标题行
        w = weight_of(text, m.start(), m.end())
        graph[aid][ref_xy] += 1
        weights[(aid, ref_xy)] = max(weights[(aid, ref_xy)], w)
        if len(examples[(aid, ref_xy)]) < 3:
            examples[(aid, ref_xy)].append(text[max(0, m.start()-30):m.end()+30].replace('\n', ' '))
        consumed.add((m.start(), m.end()))
    # 再找 X.Y
    for m in pat_xy.finditer(text):
        # 跳过已被 X.Y.Z 消费的位置
        if any(s <= m.start() < e for s, e in consumed):
            continue
        x, y = m.group(1), m.group(2)
        ref = f"{x}.{y}"
        if ref == aid or ref not in article_ids:
            continue
        if m.end() < len(text) and text[m.end()] == '\u3000':
            continue  # 全角空格 = 目录/标题行，非引用
        if m.start() > 0 and text[m.start() - 1] in '§#':
            continue  # §X.Y = 本文内部章节引用
        if m.end() < len(text) and text[m.end()] == '%':
            continue  # 百分比数据
        if m.start() > 0 and text[m.start() - 1] in '-−':
            continue  # 负号（表格/公式）
        line_start = text.rfind('\n', 0, m.start()) + 1
        if text[line_start:m.start()].strip().startswith('#'):
            continue  # Markdown 标题行
        w = weight_of(text, m.start(), m.end())
        graph[aid][ref] += 1
        weights[(aid, ref)] = max(weights[(aid, ref)], w)
        if len(examples[(aid, ref)]) < 3:
            examples[(aid, ref)].append(text[max(0, m.start()-30):m.end()+30].replace('\n', ' '))

# ---------- 3. 入边（反向） ----------
in_graph = defaultdict(Counter)
for src, dsts in graph.items():
    for dst, cnt in dsts.items():
        in_graph[dst][src] += cnt

# ---------- 4. 输出 ----------
def save():
    data = {
        'meta': {
            'articles': len(article_ids),
            'edges': sum(len(v) for v in graph.values()),
            'refs_total': sum(sum(v.values()) for v in graph.values()),
        },
        'out': {src: {dst: {'count': c, 'weight': weights[(src, dst)]}
                      for dst, c in dsts.items()}
                for src, dsts in graph.items()},
        'in': {dst: dict(srcs) for dst, srcs in in_graph.items()},
    }
    json.dump(data, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return data

def show_out(aid):
    data = json.load(open(OUT_JSON, encoding='utf-8'))
    out = data['out'].get(aid, {})
    print(f"[出边] {aid} 引用 {len(out)} 篇文章（共 {sum(v['count'] for v in out.values())} 次）:")
    for dst, v in sorted(out.items(), key=lambda kv: -kv[1]['count']):
        print(f"  → {dst:8s} x{v['count']:3d}  w{v['weight']}  {id_to_file.get(dst, '')}")
        for ex in examples.get((aid, dst), [])[:1]:
            print(f"       例: …{ex}…")

def show_in(aid):
    data = json.load(open(OUT_JSON, encoding='utf-8'))
    inn = data['in'].get(aid, {})
    print(f"[入边] {aid} 被 {len(inn)} 篇文章引用（共 {sum(inn.values())} 次）:")
    for src, cnt in sorted(inn.items(), key=lambda kv: -kv[1]):
        print(f"  ← {src:8s} x{cnt:3d}")

def show_path(src, dst):
    data = json.load(open(OUT_JSON, encoding='utf-8'))
    out = data['out']
    # BFS
    from collections import deque
    q = deque([src])
    parent = {src: None}
    while q:
        cur = q.popleft()
        if cur == dst:
            break
        for nxt in out.get(cur, {}):
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)
    if dst not in parent:
        print(f"无路径: {src} → {dst}")
        return
    path = []
    cur = dst
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    print(f"路径: {' → '.join(path)}")

def stats():
    data = json.load(open(OUT_JSON, encoding='utf-8'))
    out, inn = data['out'], data['in']
    print(f"文章总数: {data['meta']['articles']}")
    print(f"有出边的文章: {len(out)}/{data['meta']['articles']}")
    print(f"有入边的文章: {len(inn)}/{data['meta']['articles']}")
    print(f"边总数(去重): {data['meta']['edges']}, 引用总次数: {data['meta']['refs_total']}")
    # 被引 TOP
    top = sorted(inn.items(), key=lambda kv: -sum(kv[1].values()))[:15]
    print("\n被引用最多的文章 TOP15:")
    for aid, srcs in top:
        print(f"  {aid:8s} 被 {len(srcs):3d} 篇引用, {sum(srcs.values()):4d} 次")
    # 零引用
    zero = [a for a in article_ids if a not in inn]
    print(f"\n零入边文章: {len(zero)} 篇: {', '.join(sorted(zero)[:20])}")
    # 权重分布
    wcnt = Counter()
    for s, dsts in out.items():
        for d, v in dsts.items():
            wcnt[v['weight']] += 1
    print(f"\n权重分布: {dict(sorted(wcnt.items()))} (3=显式文章引用 2=章节/定理级 1=括号 0=裸编号)")

if __name__ == '__main__':
    if '--out' in sys.argv:
        show_out(sys.argv[sys.argv.index('--out') + 1])
    elif '--in' in sys.argv:
        show_in(sys.argv[sys.argv.index('--in') + 1])
    elif '--path' in sys.argv:
        i = sys.argv.index('--path')
        show_path(sys.argv[i + 1], sys.argv[i + 2])
    else:
        save()
        stats()
