#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile: 拆解 vkb.search 各环节耗时，定位 863ms 去向"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb.initialize()

def t(fn, label):
    t0 = time.perf_counter()
    r = fn()
    dt = (time.perf_counter() - t0) * 1000
    print(f'{label:42s} {dt:8.2f} ms')
    return r

QUERY = '推导精细结构常数 137.036 的完整链条'

# 1. 改写
q = t(lambda: vkb._rewrite_query(QUERY), '1. _rewrite_query (规则, 无LLM)')
print(f'    -> 改写后: {q}')

# 2. embedding（首次）
t(lambda: vkb._get_query_embedding(q), '2. _get_query_embedding (首次)')
t(lambda: vkb._get_query_embedding(q), '2b. _get_query_embedding (缓存命中)')

# 3. 向量查询
def vq():
    _qvec = vkb._get_query_embedding(q)
    return vkb._safe_collection_call('articles_collection', 'query',
                                     query_embeddings=[_qvec], n_results=30)
t(vq, '3. articles_collection.query (向量)')

# 4. BM25
t(lambda: vkb.bm25_searcher.initialized, '4. BM25 initialized 检查')
if not vkb.bm25_searcher.initialized:
    t(lambda: vkb._update_bm25_for_file('batch_auto', [], []), '4b. BM25 懒构建')
def bm():
    return vkb.bm25_searcher.search(q, top_k=15) if hasattr(vkb.bm25_searcher, 'search') else None
t(bm, '4c. BM25 search')

# 5. 完整 search（预热后）
t(lambda: vkb.search(QUERY, top_k=15), '5. search 预热(含懒构建)')
t(lambda: vkb.search(QUERY, top_k=15), '5b. search 第二次')
t(lambda: vkb.search(QUERY, top_k=15), '5c. search 第三次')

# 6. enrich_with_graph（引用图+骨架）
res = vkb.search(QUERY, top_k=15)
t(lambda: vkb.enrich_with_graph(res, QUERY), '6. enrich_with_graph (骨架注入)')
