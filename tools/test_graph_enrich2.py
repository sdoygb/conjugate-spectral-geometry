#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 enrich_with_graph 完整流程：检索 → 引用图骨架 → 骨架 chunk 注入"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app'))
from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

TASK = "精细结构常数 137.036 的完整几何推导链"

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb.initialize()
print(f"[INFO] articles_dir={vkb._articles_dir!r}")

results = vkb.search(TASK, top_k=8)
print(f"[INFO] 检索命中 {len(results)} 块")
for r in results[:8]:
    fn = r.get('metadata', {}).get('fname', '?')
    print(f"  hit: {fn[:40]} dist={r.get('distance', 0):.3f}")

merged, labels = vkb.enrich_with_graph(results, TASK)
print(f"\n[INFO] 骨架注入 {len(labels)} 块")
for lab in labels:
    print(f"  SKELETON: {lab}")

print(f"\n[INFO] 合并后总块数: {len(merged)}")
# 打印前 3 块的注入头
for r in merged[:3]:
    meta = r.get('metadata', {})
    tag = r.get('label', '')
    print(f"  top: [{meta.get('article_id', '?')} @{meta.get('start', '?')}-{meta.get('end', '?')} dist:{r.get('distance', 0):.3f}] {tag[:50]}")

# 检查骨架文章内容是否真实（抽查 2.4 和 7.5 的 chunk 开头）
print("\n[INFO] 骨架 chunk 内容抽查:")
for r in merged:
    if r.get('_skeleton'):
        meta = r.get('metadata', {})
        print(f"  --- {meta.get('fname', '?')} @{meta.get('start', '?')} ---")
        print(f"  {r['text'][:150]}...")
