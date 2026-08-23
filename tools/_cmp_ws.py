# -*- coding: utf-8 -*-
"""Workspace 新旧路径对比（子进程隔离）：结果一致性 + 延迟"""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
mode_env = os.environ.get('USE_WORKSPACE', '1')  # 从环境读取

from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

QUERY = "请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：从 δ（基础间隙）出发，给出到达 137.036 的完整推导链条。"

vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
vkb._articles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'articles')
t0 = time.time()
vkb.initialize()
t_init = time.time() - t0

# 主查询（预热 embedding 缓存后计时检索本身）
t0 = time.time()
res = vkb.search(QUERY, top_k=8)
t_search = time.time() - t0

t0 = time.time()
enh, labels = vkb.enrich_with_graph(res, QUERY)
t_enrich = time.time() - t0

top_arts = []
for r in enh[:10]:
    fn = r.get('metadata', {}).get('fname', '?')
    top_arts.append(fn.split('_')[0] if '_' in fn else fn)
skel = [l.split(':')[1].split('(')[0] for l in labels]

print(json.dumps({
    'mode': 'workspace' if vkb._use_workspace and vkb._ws else 'legacy',
    'init_ms': round(t_init * 1000),
    'search_ms': round(t_search * 1000),
    'enrich_ms': round(t_enrich * 1000),
    'n_results': len(res),
    'n_enhanced': len(enh),
    'top10': top_arts,
    'skeleton': skel,
}, ensure_ascii=False))
