#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试引用图骨架增强：137.036 推导任务，对比增强前后注入覆盖。"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app'))
from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR, MAX_INJECT_CHARS

TASK = "请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：从 δ（基础间隙）出发，给出到达 α⁻¹ = 137.036 的完整推导链条。"

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb.initialize()

# 1. 无增强：模拟现有管道
results = vkb.search(TASK, top_k=8)
content, chunks = vkb.get_formatted_results(results)
ids_before = sorted({r.get('metadata', {}).get('fname', '?')[:8] for r in results})
print(f"=== 增强前 ===")
print(f"注入字符: {len(content)} / {MAX_INJECT_CHARS}")
print(f"命中文章: {ids_before}")
print(f"前3块标题: {[r['label'][:60] for r in results[:3]]}")

# 2. 增强后
enhanced, gchunks = vkb.enrich_with_graph(results, TASK)
content2, chunks2 = vkb.get_formatted_results(enhanced)
ids_after = []
for r in enhanced:
    fn = r.get('metadata', {}).get('fname', '?')[:8]
    tag = 'SKELETON' if r.get('_skeleton') else 'normal'
    ids_after.append(f"{tag}:{fn}")
print(f"\n=== 增强后 ===")
print(f"骨架注入: {gchunks}")
print(f"注入字符: {len(content2)} / {MAX_INJECT_CHARS}")
print(f"注入顺序: {ids_after}")
print(f"\n=== 骨架文章是否包含推导链核心 ===")
core = ['2.6', '0.8', '2.1', '1.5', '7.5', '2.4']
for c in core:
    hit = any(c in g or c in str(ids_after) for g in gchunks) or c in str(ids_after)
    print(f"  {c}: {'✔' if hit else '✘'}")
