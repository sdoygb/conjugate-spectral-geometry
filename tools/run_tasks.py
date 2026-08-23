#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多任务压力测试：6 个不同领域的推导任务，验证 Workspace v2 管线的稳定性
用法：python3 run_tasks.py [--only T1,T2] [--results results.json]
断点续跑：结果已存在的任务跳过（--force 重跑）
"""
import os, sys, json, time, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'app'))

from workspace_core import Workspace, run_task, call_llm, GAI_API_KEY, GAI_BASE_URL, GAI_MODEL_LITE

TASKS = {
    'T1_alpha': {
        'name': '精细结构常数 α⁻¹=137.036',
        'task': "请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：\n"
                "从 δ（基础间隙）出发，给出到达 α⁻¹ = 137.036 的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号（如 2.6、1.5、0.8）\n"
                "3. 给出关键公式（如 S(σ*) 的显式形式）\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出，从 δ 开始到 137.036 结束。",
    },
    'T2_surface': {
        'name': '水的表面张力 γ≈0.072 N/m',
        'task': "请完整推导水的表面张力 γ ≈ 0.072 N/m 的几何来源：\n"
                "从界面自由能出发，给出到达 0.072 N/m 的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号\n"
                "3. 给出关键公式（如 γ 的显式形式，含热能标度与几何本征值）\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出。",
    },
    'T3_lepton': {
        'name': '三代轻子质量比 m_μ/m_e',
        'task': "请完整推导三代轻子质量刚性（如 μ/e 质量比 ≈ 206.77 或三代质量结构）的几何来源：\n"
                "从几何框架出发，给出到达轻子质量比的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号\n"
                "3. 给出关键公式与数值\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出。",
    },
    'T4_higgs': {
        'name': 'Higgs 质量 m_H≈125.64 GeV',
        'task': "请完整推导 Higgs 质量 m_H ≈ 125.64 GeV 的几何来源：\n"
                "从联络曲率刚度出发，给出到达 125.64 GeV 的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号\n"
                "3. 给出关键公式（如 m_H 与曲率刚度的关系）\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出。",
    },
    'T5_timeEnt': {
        'name': '时间纠缠几何相位 δ_φ',
        'task': "请完整推导时间纠缠熵 S_ent 及其可检验信号 δ_φ(Δη,Δξ)（双光子干涉相位偏移）的几何来源：\n"
                "从时间纠缠判据出发，给出 δ_φ 的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号\n"
                "3. 给出关键公式（如 δ_φ 的显式函数形式与数值窗口）\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出。",
    },
    'T6_qec': {
        'name': '量子纠错码错误率标度律',
        'task': "请完整推导量子纠错码（CSS 码/里德-米勒码族）错误率随码距 d 的标度律的几何来源：\n"
                "从码的结构出发，给出错误率标度（如 P_fail ∝ (d/2)^{-d/2}）的完整推导链条。\n"
                "要求：\n1. 链条每一步说明机制（输入→操作→输出）\n"
                "2. 每一步标注来源文章编号\n"
                "3. 给出关键公式（标度律的显式形式）\n"
                "4. 如果某一步没有可靠来源，明确标注【未验证】\n"
                "请以\"推导链\"形式输出。",
    },
}

def load_results(path):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding='utf-8'))
        except Exception:
            return {}
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='逗号分隔的任务 ID 列表，如 T1_alpha,T2_surface')
    ap.add_argument('--results', default='task_results.json', help='结果文件路径')
    ap.add_argument('--force', action='store_true', help='重跑已有任务')
    args = ap.parse_args()

    results_path = os.path.join(ROOT, 'tools', args.results)
    results = load_results(results_path)

    if args.only:
        ids = [x.strip() for x in args.only.split(',') if x.strip()]
    else:
        ids = list(TASKS.keys())
    todo = [i for i in ids if args.force or i not in results]

    if not todo:
        print("所有任务已完成（或指定任务不存在）。使用 --force 重跑。")
        return

    # 初始化（一次性，所有任务共享）
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    from openai import OpenAI

    articles_dir = os.path.join(ROOT, 'app', 'articles')
    t0 = time.time()
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()
    ws = Workspace(vkb, articles_dir)
    load_t = ws.load_all()
    print(f"[init] {time.time()-t0:.1f}s (全量加载 {load_t:.1f}s), "
          f"矩阵 {ws._data['matrix'].shape}, 摘要 {len(ws._summaries)} 篇")
    client = OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)

    for tid in todo:
        meta = TASKS[tid]
        print(f"\n===== {tid} | {meta['name']} =====")
        t0 = time.time()
        res = run_task(ws, client, meta['task'], tid)
        res['name'] = meta['name']
        res['elapsed_s'] = round(time.time() - t0, 1)
        results[tid] = res
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        rpt = res['integrity']
        print(f"完成: {res['rounds']} 轮, tokens={res['token_total']} "
              f"(in={res['prompt_tokens']}), 悬空={len(rpt['dangling'])} "
              f"缺口={len(rpt['gaps'])}, 检索 {res['t_retrieval_s']}s 生成 {res['t_generation_s']}s")
        print(f"骨架: {res['skeleton']}, 命中文章: {res['hit_aids']}")

    print(f"\n===== 汇总 ({len(results)}/{len(TASKS)} 任务完成) =====")
    for tid, r in results.items():
        print(f"{tid}: {r.get('name','')} | {r['rounds']}轮 | tokens={r['token_total']} | "
              f"悬空={len(r['integrity']['dangling'])} 缺口={len(r['integrity']['gaps'])} | {r.get('elapsed_s','?')}s")
    print(f"缓存: hits={ws.hits} misses={ws.misses}")
    print(f"结果: {results_path}")

if __name__ == '__main__':
    main()
