#!/usr/bin/env python3
"""延迟拆解：embedding API vs chroma 本地检索 vs 完整 search"""
import os, sys, time
APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app')
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)
import logging
logging.disable(logging.WARNING)
from knowledge import VectorKnowledgeBase

kb = VectorKnowledgeBase(persist_dir=os.path.join(APP_DIR, 'chroma_db'))
kb.initialize()
kb.search("热身", top_k=3)

# 1) embedding API 单独延迟（SiliconFlow bge-large-zh-v1.5）
from knowledge import SiliconFlowEmbeddingFunction
sf = kb.embedding_fn
t0 = time.perf_counter()
vec = sf(["谱条件窗口 100到200 可生存观测者位置"])
t_emb = (time.perf_counter() - t0) * 1000
print(f"[embedding API 单次] {t_emb:.0f}ms  dim={len(vec[0])}")

# 2) chroma 本地检索延迟（用已算好的向量，纯 ANN 搜索）
col = kb.articles_collection
times = []
for _ in range(5):
    t0 = time.perf_counter()
    col.query(query_embeddings=[vec[0]], n_results=5)
    times.append((time.perf_counter() - t0) * 1000)
print(f"[chroma 本地检索] 5次: {[f'{t:.0f}' for t in times]}ms  中位 {sorted(times)[2]:.0f}ms")

# 3) 完整 search 延迟（含改写+embedding+检索+锚点+重排）
for q in ["谱条件窗口 100到200 可生存观测者位置", "弱透镜 宇宙剪切 噪声 异常检测 比赛"]:
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        res = kb.search(q, top_k=5)
        times.append((time.perf_counter() - t0) * 1000)
    print(f"\n[search完整: {q[:16]}...] 3次: {[f'{t:.0f}' for t in times]}ms")
    for r in res[:5]:
        fname = (r.get('metadata') or {}).get('fname', '?')
        print(f"    {fname}@{r.get('distance',0):.3f} | {r.get('text','')[:60]}")

# 4) 缓存命中延迟（同一 query 第二次）
q = "色码 crossing lift A0 A1 阈值"
kb.search(q, top_k=5)
t0 = time.perf_counter()
kb.search(q, top_k=5)
print(f"\n[query缓存命中] {((time.perf_counter()-t0)*1000):.0f}ms")
