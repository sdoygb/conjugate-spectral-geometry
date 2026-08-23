#!/usr/bin/env python3
"""向量库检索基准：端到端延迟 + 命中质量（对照应用层真实路径）"""
import os, sys, time, json

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app')
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

import logging
logging.disable(logging.WARNING)

from knowledge import VectorKnowledgeBase

kb = VectorKnowledgeBase(persist_dir=os.path.join(APP_DIR, 'chroma_db'))
t0 = time.perf_counter()
ok = kb.initialize()
print(f"init: {ok} | {time.perf_counter()-t0:.2f}s | articles: {kb.articles_count}")

# 热身：触发 BM25 懒构建（首次 search 会全量建索引）
t0 = time.perf_counter()
kb.search("热身", top_k=3)
print(f"warmup(BM25构建): {time.perf_counter()-t0:.2f}s")

QUERIES = [
    ("Q1 谱条件窗口", "谱条件窗口 100到200 可生存观测者位置", "2.4"),
    ("Q2 S_e七级递推锁定", "S_e 七级递推 Born归一化 唯一确定 可调自由度为零", "10.14"),
    ("Q3 七级递推显式公式", "S_0=137 到 S_7=S_e 的显式递推公式 每级步骤 如何算出", "未知(上次缺口)"),
    ("Q4 色码crossing lift", "色码 crossing lift A0 A1 阈值 码距退化", "10.54/10.55"),
    ("Q5 N1=6000标度基数", "N_1=6000 整数标度基数 小数位几何投影 量子化层锁定", "8.15"),
    ("Q6 观测者位置输入", "观测者位置 输入参数 不是公理推论 精细结构常数", "1.5/10.23"),
    ("Q7 Prandtl角度比", "Prandtl 数 1.92 角度比 湍流 动量扩散", "10.8/5.x"),
    ("Q8 格密码量子攻击", "格密码 量子攻击 谱刚性带 定理", "10.56"),
    ("Q9 弱透镜OoD", "弱透镜 宇宙剪切 噪声 异常检测 比赛", "kappa-lab/9.x"),
    ("Q10 Reed-Muller", "Reed-Muller CSS 码 精确损失标度 阈值", "QEC_Paper_EN"),
    ("Q11 中微子质量", "中微子 质量 振荡 混合角", "10.x"),
    ("Q12 超导材料筛选", "超导 材料 筛选 定理 临界温度", "topo_sc"),
]

report = []
for tag, q, expect in QUERIES:
    t0 = time.perf_counter()
    res = kb.search(q, top_k=5)
    dt = (time.perf_counter() - t0) * 1000
    hits = []
    for r in res[:5]:
        fname = (r.get('metadata') or {}).get('fname', '?')
        hits.append(f"{fname}@{r.get('distance', 0):.3f}")
    report.append({"tag": tag, "ms": round(dt), "expect": expect, "top5": hits})
    print(f"\n[{tag}] {dt:.0f}ms  预期:{expect}")
    for h in hits:
        print(f"    {h}")

print("\n=== 汇总 ===")
for r in report:
    print(f"{r['tag']:24s} {r['ms']:6d}ms  预期[{r['expect']}]  ->  {', '.join(r['top5'][:3])}")
