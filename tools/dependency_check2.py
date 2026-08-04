#!/usr/bin/env python3
"""依赖检查v2：从已入库定理的源文章提取引用，与主库比对"""
import os, re, json, glob
import chromadb

client = chromadb.PersistentClient(path='master_ai/master_chroma_db')
col = client.get_collection('master_formulas')
data = col.get(include=['metadatas'])

master_nums = set()
admitted = []  # (article_number, source_article, formula_name)
for m in data['metadatas']:
    if m.get('article_number'):
        master_nums.add(m['article_number'])
    if m.get('source_agent','').startswith('local_ai_manual_260805'):
        sa = ''
        try:
            vr = json.loads(m.get('verification_result','{}'))
            sm = vr.get('summary','')
            mm = re.search(r'来源文章 (.+?\.md)', sm)
            if mm: sa = mm.group(1)
        except: pass
        admitted.append((m.get('article_number'), sa, m.get('formula_name')))

print(f"本轮入库: {len(admitted)} 条")

# 文章路径映射：按文件名找
art_map = {}
for p in glob.glob('app/articles/**/*.md', recursive=True):
    if '/archive/' in p or 'archive' in p.split('/'):
        continue
    art_map[os.path.basename(p)] = p

REF_PAT = re.compile(r'(定理|引理|命题|推论|公理|定义)\s*(\d+\.\d+\.\d+\.\d+)')
def declared_nums(path):
    nums = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            if re.match(r'\s*#|^\*\*?(定理|引理|命题|推论|公理|定义)\s*\d', line):
                mm = re.search(r'(定理|引理|命题|推论|公理|定义)\s*(\d+\.\d+\.\d+\.\d+)', line)
                if mm: nums.add(mm.group(2))
    return nums

# 对每条已入库定理：扫描源文章全部引用
dangling_per_theorem = []  # (formula_name, art, 悬空编号列表)
no_article = []
for num, sa, fname in admitted:
    if not sa or sa not in art_map:
        no_article.append((fname, sa))
        continue
    path = art_map[sa]
    declared = declared_nums(path)
    with open(path, encoding='utf-8') as f:
        text = f.read()
    refs = set(m.group(2) for m in REF_PAT.finditer(text)) - declared
    dangling = sorted(refs - master_nums)
    if dangling:
        dangling_per_theorem.append((fname, sa, dangling))

print(f"\n=== 悬空依赖（引用了不在主库的定理） ===")
seen_arts = set()
all_dangling = set()
for fname, sa, d in dangling_per_theorem:
    if sa not in seen_arts:
        seen_arts.add(sa)
        print(f"\n{sa}:")
        for n in d:
            print(f"  - {n}")
            all_dangling.add(n)
if not dangling_per_theorem:
    print("（无）")

print(f"\n=== 悬空编号声明位置 ===")
declared_where = {}
for p in glob.glob('app/articles/**/*.md', recursive=True):
    for n in declared_nums(p):
        declared_where.setdefault(n, []).append(os.path.basename(p))
for n in sorted(all_dangling):
    print(f"{n}: {declared_where.get(n, '未找到声明')}")

# 未找到文章的入库定理
if no_article:
    print(f"\n=== 无法定位源文章（{len(no_article)}条） ===")
    for fname, sa in no_article[:10]:
        print(f"  {fname} | {sa}")
