#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证实验：flash 无检索 vs flash+检索循环 vs pro 无检索
任务：推导 α⁻¹=137.036 的完整几何来源链（从 δ 到 137.036）
三组统一关闭 thinking（隔离变量：验证检索注入能否补推理短板）
附带检查：现有注入机制是否合理（注入量、格式、flash 可用性）
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


def build_retrieval_inject(vkb):
    """真实检索管道：模拟'多搜索'第一轮（与生产完全一致）"""
    results = vkb.search(TASK, top_k=8)
    inject = []
    meta_stats = []
    for r in results[:6]:
        meta = r.get('metadata', {})
        aid = meta.get('article_id', '?')
        text = r.get('text', '')
        header = f"[{aid} @{meta.get('start','?')}-{meta.get('end','?')} dist:{r.get('distance',0):.3f}]"
        inject.append(header + text[:900])
        meta_stats.append({"article": aid, "dist": round(r.get('distance', 0), 3),
                           "chars": len(text)})
    inject_text = "\n\n".join(inject)
    return inject_text, meta_stats, results


def main():
    import sys as _sys
    only = _sys.argv[1] if len(_sys.argv) > 1 else 'all'
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()

    # ---- 真实检索注入（B 组用）----
    inject_text, meta_stats, results = build_retrieval_inject(vkb)
    print("=== 检索注入统计（B 组） ===")
    for s in meta_stats:
        print(f"  {s['article']}  dist={s['dist']}  {s['chars']}字符")
    print(f"  注入总字符: {len(inject_text)}")

    sys_b = SYS_BASE + "\n\n【参考资料（真实检索结果，必须优先使用并标注来源）】\n" + inject_text

    groups = [
        ("A_flash_no_retrieval", GAI_MODEL_LITE, SYS_BASE),
        ("B_flash_with_retrieval", GAI_MODEL_LITE, sys_b),
        ("C_pro_no_retrieval", GAI_MODEL, SYS_BASE),
    ]

    client = OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)
    out = {"task": TASK, "retrieval_stats": meta_stats, "groups": {}}

    for name, model, sys_p in groups:
        if only != 'all' and not name.startswith(only):
            continue
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_p},
                    {"role": "user", "content": TASK},
                ],
                temperature=0.3,
                max_tokens=int(os.environ.get('MY_MAX_TOKENS', '4000')),
                extra_body={'thinking': {'type': 'disabled'}},
            )
            content = resp.choices[0].message.content or ''
            reasoning = getattr(resp.choices[0].message, 'reasoning_content', None) or ''
            usage = resp.usage
            out["groups"][name] = {
                "output": content,
                "reasoning": reasoning,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "time_s": round(time.time() - t0, 1),
                "sys_prompt_chars": len(sys_p),
                "finish_reason": resp.choices[0].finish_reason,
            }
            print(f"[{name}] tokens={usage.total_tokens} "
                  f"(in={usage.prompt_tokens}, out={usage.completion_tokens}) "
                  f"time={out['groups'][name]['time_s']}s finish={resp.choices[0].finish_reason}")
        except Exception as e:
            out["groups"][name] = {"error": str(e)}
            print(f"[{name}] ERROR: {e}")

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_experiment_results')
    # 合并已有结果（避免覆盖其他组）
    merged = {}
    if os.path.exists(base + '.json'):
        try:
            merged = json.load(open(base + '.json', encoding='utf-8'))
        except Exception:
            merged = {}
    merged['task'] = out['task']
    merged['retrieval_stats'] = out['retrieval_stats']
    merged.setdefault('groups', {}).update(out['groups'])
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print("\n已保存: tools/verify_experiment_results.json")


if __name__ == '__main__':
    main()
