#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 rerank 分歧检测闸门：延迟 + 质量"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb.initialize()

QUERIES = [
    '推导精细结构常数 137.036 的完整链条',
    '证明谱条件窗口 100 到 200 的几何来源',
    '什么是观测者位置 sigma*',
    '中微子振荡的几何解释',
    '区域生命周期的十二步是什么',
    '混合矩阵的生成顺序',
]

for q in QUERIES:
    t0 = time.perf_counter()
    res = vkb.search(q, top_k=15)
    dt = (time.perf_counter() - t0) * 1000
    arts = [r for r in res if r.get('source') == 'articles']
    pool = arts[:40]
    disagree = vkb._rerank_disagreement(pool) if len(pool) >= 3 else None
    # 强制 rerank 对比（绕过闸门）
    docs = [r.get('text', '')[:600] for r in pool]
    rr = vkb._rerank(q, docs, top_n=10) if len(pool) >= 3 else None
    reranked_top5 = []
    if rr and rr.get('results'):
        scores = {it['index']: it['relevance_score'] for it in rr['results']}
        pool_sorted = sorted(pool, key=lambda r: scores.get(pool.index(r), 0), reverse=True)
        reranked_top5 = [r.get('metadata', {}).get('fname', '?')[:30] for r in pool_sorted[:5]]
    else:
        reranked_top5 = ['(rerank失败/跳过)']
    rrf_top5 = [r.get('metadata', {}).get('fname', '?')[:30] for r in sorted(pool, key=lambda x: -x.get('_rrf_score', 0))[:5]]
    print(f'[{q[:22]}] search={dt:6.0f}ms | 分歧={disagree} | rerank调={rr is not None and bool(rr.get("results"))}')
    print(f'    RRF top5 : {rrf_top5}')
    print(f'    Rerank top5: {reranked_top5}')
