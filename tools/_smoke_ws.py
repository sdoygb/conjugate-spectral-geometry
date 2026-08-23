# -*- coding: utf-8 -*-
"""Workspace 转正冒烟测试：初始化、检索、骨架、新旧对比"""
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))

from knowledge import VectorKnowledgeBase
from config import CHROMA_DB_DIR

TASKS = [
    "请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：从 δ（基础间隙）出发，给出到达 137.036 的完整推导链条。要求：1. 链条每一步说明机制；2. 每一步标注来源文章编号；3. 给出关键公式；4. 没有可靠来源的步骤明确标注【未验证】。",
    "请推导水的表面张力 γ ≈ 0.072 N/m 的几何来源：从界面自由能出发，给出到达 0.072 N/m 的完整推导链条。要求同上。",
]

def run(name, use_ws):
    os.environ['USE_WORKSPACE'] = '1' if use_ws else '0'
    import importlib
    import knowledge as K
    importlib.reload(K)
    vkb = K.VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb._articles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'articles')
    t0 = time.time()
    ok = vkb.initialize()
    t_init = time.time() - t0
    print(f"\n=== {name}: init={t_init*1000:.0f}ms use_workspace={vkb._use_workspace} ws={'ready' if vkb._ws else 'None'} ===")
    if not ok:
        print("初始化失败")
        return None
    for i, q in enumerate(TASKS):
        t0 = time.time()
        res = vkb.search(q, top_k=8)
        t_s = time.time() - t0
        t0 = time.time()
        enh, labels = vkb.enrich_with_graph(res, q)
        t_e = time.time() - t0
        arts = [r.get('metadata', {}).get('fname', '?') for r in enh]
        print(f"  T{i+1}: search={t_s*1000:.0f}ms enrich={t_e*1000:.0f}ms 结果{len(res)}条→增强{len(enh)}条")
        print(f"    骨架: {labels[:3]}")
        print(f"    前8 fname: {[a[:20] for a in arts[:8]]}")
    return vkb

if __name__ == '__main__':
    v1 = run("Workspace 开", True)
    # 结果写入临时文件对比
    v2 = run("Workspace 关", False)
    print("\n=== 完成 ===")
