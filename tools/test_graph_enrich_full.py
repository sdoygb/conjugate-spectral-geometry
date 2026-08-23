#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""enrich_with_graph 完整流程验证：检索 → 引用图骨架增强 → 骨架 chunk 拉取"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app'))
from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

QUERY = '精细结构常数 137.036 推导 完整链条'

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb.initialize()
print('articles_dir:', repr(vkb._articles_dir))

results = vkb.search(QUERY, top_k=8)
print('检索命中:', len(results))
for r in results[:5]:
    meta = r.get('metadata', {})
    print('  命中:', meta.get('fname', '?')[:44], f"dist={r.get('distance', 0):.3f}")

enhanced, labels = vkb.enrich_with_graph(results, QUERY)
print('增强后总块数:', len(enhanced))
print('骨架标签:', labels)
print('--- 前 6 块（骨架应在前）---')
for r in enhanced[:6]:
    meta = r.get('metadata', {})
    tag = '[SKELETON]' if r.get('_skeleton') else '[semantic]'
    print(f"  {tag} {meta.get('fname', '?')[:44]} @{meta.get('start', '?')}-{meta.get('end', '?')} dist={r.get('distance', 0):.3f}")
    if r.get('_skeleton'):
        print('      首句:', r['text'][:60].replace('\n', ' '))
