#!/usr/bin/env python3
"""依赖检查：从源文章提取定理引用，与主库比对，找出悬空依赖"""
import os, re, json, glob
import chromadb

# 1. 主库现有编号
client = chromadb.PersistentClient(path='master_ai/master_chroma_db')
col = client.get_collection('master_formulas')
data = col.get(include=['metadatas'])
master_nums = set()
for m in data['metadatas']:
    if m.get('article_number'):
        master_nums.add(m['article_number'])

print(f"主库定理数: {len(master_nums)}")

# 2. 扫描文章，提取引用
REF_PAT = re.compile(r'(定理|引理|命题|推论|公理|定义)\s*(\d+\.\d+\.\d+\.\d+)')
ART_PAT = re.compile(r'\*\*?(定理|引理|命题|推论|公理|定义)\s*(\d+\.\d+\.\d+\.\d+)')

# 卷1-10文章
articles = sorted(glob.glob('app/articles/EN/[0-9]*/*.md') + glob.glob('app/articles/[0-9]*.md') + glob.glob('app/articles/*.md'))
# 只保留 1.x ~ 10.x
articles = [a for a in articles if re.search(r'[1-9][0-9]?\.', os.path.basename(a))]

# 每篇文章自己声明的定理编号（排除自身引用）
def declared_nums(path):
    nums = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = ART_PAT.match(line.strip())
            if m:
                nums.add(m.group(2))
    return nums

# 3. 对每篇已入库定理的文章，找悬空引用
# 先收集所有已入库定理的 source_article
from collections import defaultdict
admitted_articles = set()
for m in data['metadatas']:
    if m.get('source_agent', '').startswith('local_ai_manual_260805'):
        admitted_articles.add(m.get('source_article', ''))

print(f"已入库(本轮)定理所在文章数: {len(admitted_articles)}")

# 悬空引用统计
dangling = defaultdict(set)   # 文章 -> set(悬空编号)
article_declared = {}         # 文章 -> 自身声明编号
for art in articles:
    base = os.path.basename(art)
    if base not in admitted_articles:
        continue
    declared = declared_nums(art)
    article_declared[base] = declared
    with open(art, encoding='utf-8') as f:
        text = f.read()
    for m in REF_PAT.finditer(text):
        num = m.group(2)
        if num in declared:
            continue  # 自身声明，不是引用
        if num not in master_nums:
            dangling[base].add(num)

print(f"\n=== 悬空依赖报告（卷1-10 已入库文章） ===")
total = 0
for art in sorted(dangling):
    nums = sorted(dangling[art])
    print(f"\n{art}: {len(nums)} 个悬空引用")
    for n in nums:
        print(f"  - {n}")
    total += len(nums)
print(f"\n总计悬空引用: {total}")

# 4. 这些悬空引用对应的定理声明在哪里？（可能在未入库的卷）
# 搜索所有文章里声明了这些编号的位置
dangling_all = set()
for s in dangling.values():
    dangling_all |= s
print(f"\n=== 悬空编号在哪些文章中被声明 ===")
for n in sorted(dangling_all):
    where = []
    for art in articles:
        if n in article_declared.get(os.path.basename(art), set()):
            where.append(os.path.basename(art))
    print(f"{n}: 声明于 {where if where else '未找到(可能编号错误或仅口头引用)'}")
