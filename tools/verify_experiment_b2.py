#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B2 组实验：flash + 增强注入（search + enrich_with_graph 引用图骨架注入，与生产路径一致）
对比 B 组（旧：仅 search 注入），验证引用图融合注入的价值。
任务：推导 α⁻¹=137.036 的完整几何来源链（从 δ 到 137.036）。
统一关闭 thinking（隔离变量：验证注入内容差异）。
"""
import os, sys, time, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from openai import OpenAI
from config import GAI_API_KEY, GAI_BASE_URL, GAI_MODEL, GAI_MODEL_LITE

TASK = """请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：
从 δ（基础间隙）出发，给出到达 α⁻¹ = 137.036 的完整推导链条。
要求：
1. 链条每一步说明机制（输入→操作→输出）
2. 每一步标注来源文章编号（如 2.6、1.5、0.8）
3. 给出关键公式（如 S(σ*) 的显式形式）
4. 如果某一步没有可靠来源，明确标注【未验证】
请以"推导链"形式输出，从 δ 开始到 137.036 结束。"""

SYS_BASE = """你是严格基于几何论文章库回答问题的共扼谱几何专家。所有结论必须可追溯，宁缺毋滥。"""


def build_retrieval_inject_v2(vkb):
    """增强注入：search + enrich_with_graph（引用图骨架注入，与生产路径一致）"""
    results = vkb.search(TASK, top_k=8)
    enhanced, labels = vkb.enrich_with_graph(results, TASK)
    inject = []
    meta_stats = []
    for r in enhanced[:8]:
        meta = r.get('metadata', {})
        aid = meta.get('article_id', '?')
        text = r.get('text', '')
        if r.get('label'):
            header = f"[{r['label']}]"
        else:
            header = f"[{aid} @{meta.get('start','?')}-{meta.get('end','?')} dist:{r.get('distance',0):.3f}]"
        inject.append(header + text[:900])
        meta_stats.append({
            "article": aid, "label": r.get('label', ''),
            "dist": round(r.get('distance', 0), 3), "chars": len(text)
        })
    inject_text = "\n\n".join(inject)
    return inject_text, meta_stats, labels


def main():
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()

    inject_text, meta_stats, labels = build_retrieval_inject_v2(vkb)
    print("=== B2 增强注入统计（search + 引用图骨架） ===")
    for s in meta_stats:
        tag = s['label'] or s['article']
        print(f"  {tag}  dist={s['dist']}  {s['chars']}字符")
    print(f"  骨架: {labels}")
    print(f"  注入总字符: {len(inject_text)}")

    sys_b2 = SYS_BASE + "\n\n【参考资料（真实检索结果+引用图骨架，必须优先使用并标注来源）】\n" + inject_text

    client = OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)
    name = "B2_flash_with_graph_inject"
    t0 = time.time()
    resp = client.chat.completions.create(
        model=GAI_MODEL_LITE,
        messages=[
            {"role": "system", "content": sys_b2},
            {"role": "user", "content": TASK},
        ],
        temperature=0.3,
        max_tokens=int(os.environ.get('MY_MAX_TOKENS', '4000')),
        extra_body={'thinking': {'type': 'disabled'}},
    )
    content = resp.choices[0].message.content or ''
    reasoning = getattr(resp.choices[0].message, 'reasoning_content', None) or ''
    usage = resp.usage
    entry = {
        "output": content,
        "reasoning": reasoning,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "time_s": round(time.time() - t0, 1),
        "sys_prompt_chars": len(sys_b2),
        "finish_reason": resp.choices[0].finish_reason,
    }
    print(f"[{name}] tokens={usage.total_tokens} "
          f"(in={usage.prompt_tokens}, out={usage.completion_tokens}) "
          f"time={entry['time_s']}s finish={resp.choices[0].finish_reason}")

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_experiment_results')
    merged = {}
    if os.path.exists(base + '.json'):
        try:
            merged = json.load(open(base + '.json', encoding='utf-8'))
        except Exception:
            merged = {}
    merged.setdefault('groups', {})[name] = entry
    merged['b2_retrieval_stats'] = meta_stats
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print("\n已保存 B2 组: tools/verify_experiment_results.json")


if __name__ == '__main__':
    main()
