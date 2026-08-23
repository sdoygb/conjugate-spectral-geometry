#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迭代检索原型：全量摘要地图 + 推理驱动按需拉取
- 第一轮：动态检索（暴力向量 + 动态引用骨架）+ 180 篇文章摘要地图 → LLM 生成
- 完整性检查：提取输出引用编号（悬空检测）+【未验证】标注（缺口检测）
- 后续轮：针对缺口上下文发起新检索 → 追加注入 → LLM 修正
- 直到链条完整（无缺口、无悬空引用）或达到轮次上限
"""
import os, re, json, glob, sys, time
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'app'))
from config import GAI_API_KEY, GAI_BASE_URL, GAI_MODEL_LITE

# ---------- 引用提取正则（与 build_citation_graph 一致） ----------
pat_xyz = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})\.(\d{1,2})(?![0-9.])')
pat_xy  = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])')
W3_WORDS = ['文章', '详见', '参见', '参考', '见', '引用', '综述', '依赖']
W2_AFTER = ['§', '附录', '章', '节', '定理', '引理', '命题', '推论', '注', '公理']
W2_BEFORE = ['定理', '引理', '命题', '推论', '公理', '见', '参考', '详见']

def strip_math(text):
    text = re.sub(r'\$[^$]*\$', ' ', text)
    text = re.sub(r'\\\(.*?\\\)', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', ' ', text, flags=re.DOTALL)
    return text

def strip_toc(text):
    return re.sub(r'##\s*目\s*录.*?(?=\n##|\n---|\Z)', '', text, flags=re.DOTALL)

def weight_of(text, start, end):
    before = text[max(0, start - 20):start]
    after = text[end:end + 20]
    for w in W3_WORDS:
        if w in before:
            return 3
    for w in W2_BEFORE:
        if w in before:
            return 2
    for w in W2_AFTER:
        if w in after:
            return 2
    if start > 0 and text[start - 1] in '（(':
        return 1
    return 0

# ---------- 动态引用图（mtime 缓存，文章更新即失效） ----------
class DynamicGraph:
    def __init__(self, articles_dir):
        self.articles_dir = articles_dir
        self._graph = None
        self._sig = None
        self.article_ids = set()

    def _scan(self):
        files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
        ids, id2file = set(), {}
        for f in files:
            m = re.match(r'^(\d{1,2})\.(\d{1,2})_', os.path.basename(f))
            if m:
                aid = f"{m.group(1)}.{m.group(2)}"
                ids.add(aid)
                id2file[aid] = f
        graph = defaultdict(Counter)
        for aid, f in id2file.items():
            raw = open(f, encoding='utf-8').read()
            text = strip_toc(strip_math(raw))
            consumed = set()
            for m in pat_xyz.finditer(text):
                ref = f"{m.group(1)}.{m.group(2)}"
                if ref == aid or ref not in ids:
                    continue
                if m.end() < len(text) and text[m.end()] == '\u3000':
                    continue
                if m.start() > 0 and text[m.start() - 1] in '§#':
                    continue
                if m.end() < len(text) and text[m.end()] == '%':
                    continue
                if m.start() > 0 and text[m.start() - 1] in '-−':
                    continue
                line_start = text.rfind('\n', 0, m.start()) + 1
                if text[line_start:m.start()].strip().startswith('#'):
                    continue
                graph[aid][ref] += 1
                consumed.add((m.start(), m.end()))
            for m in pat_xy.finditer(text):
                if any(s <= m.start() < e for s, e in consumed):
                    continue
                ref = f"{m.group(1)}.{m.group(2)}"
                if ref == aid or ref not in ids:
                    continue
                if m.end() < len(text) and text[m.end()] == '\u3000':
                    continue
                if m.start() > 0 and text[m.start() - 1] in '§#':
                    continue
                if m.end() < len(text) and text[m.end()] == '%':
                    continue
                if m.start() > 0 and text[m.start() - 1] in '-−':
                    continue
                line_start = text.rfind('\n', 0, m.start()) + 1
                if text[line_start:m.start()].strip().startswith('#'):
                    continue
                graph[aid][ref] += 1
                consumed.add((m.start(), m.end()))
        return graph, ids, id2file

    def build(self):
        files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
        sig = tuple((f, os.path.getmtime(f)) for f in files)
        if sig != self._sig or self._graph is None:
            self._graph, self.article_ids, _ = self._scan()
            self._sig = sig
        return self._graph

    def skeleton(self, graph, hit_aids, top=3):
        out_cnt, in_cnt = Counter(), Counter()
        for a in hit_aids:
            for dst, c in graph.get(a, {}).items():
                out_cnt[dst] += c
        for src, dsts in graph.items():
            for dst, c in dsts.items():
                if dst in hit_aids:
                    in_cnt[src] += c
        hub = out_cnt + in_cnt
        return [a for a, _ in hub.most_common(top)]

# ---------- 摘要地图 ----------
def extract_summaries(articles_dir):
    files = sorted(glob.glob(os.path.join(articles_dir, '*.md')))
    lines = []
    for f in files:
        m = re.match(r'^(\d{1,2})\.(\d{1,2})_', os.path.basename(f))
        if not m:
            continue
        aid = f"{m.group(1)}.{m.group(2)}"
        raw = open(f, encoding='utf-8').read()
        tm = re.search(r'^#\s+(.+)$', raw, re.M)
        title = tm.group(1).strip() if tm else ''
        am = re.search(r'##\s*摘要\s*\n+(.+?)(?:\n\n|\n---|\Z)', raw, re.DOTALL)
        abs_text = ''
        if am:
            abs_text = re.sub(r'\s+', ' ', am.group(1)).strip()
            abs_text = re.sub(r'\$[^$]*\$', '', abs_text)
            abs_text = re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]', '', abs_text)
            abs_text = re.sub(r'\s+', ' ', abs_text).strip()
        if len(abs_text) > 130:
            abs_text = abs_text[:130] + '…'
        lines.append(f"{aid} {title}：{abs_text}")
    return lines

# ---------- 动态检索（暴力向量 + 主题锚定 + 动态骨架） ----------
class DynamicRetriever:
    def __init__(self, vkb, dg):
        self.vkb = vkb
        self.dg = dg
        self._data = None

    def _load_all(self):
        if self._data is None:
            col = self.vkb.articles_collection
            got = col.get(include=['embeddings', 'metadatas', 'documents'])
            ids = got['ids']
            embs = np.array(got['embeddings'], dtype=np.float32)
            metas = got['metadatas']
            docs = got['documents']
            aids = []
            for meta in metas:
                fn = meta.get('article_id', '?')
                mm = re.match(r'^(\d{1,2})\.(\d{1,2})', fn)
                aids.append(f"{mm.group(1)}.{mm.group(2)}" if mm else fn)
            self._data = {'ids': ids, 'matrix': embs, 'metas': metas, 'docs': docs, 'aids': aids}
        return self._data

    def search(self, query, top_k=8, skeleton_k=3):
        data = self._load_all()
        q = self.vkb._get_query_embedding(query)
        scores = data['matrix'] @ q
        top_idx = np.argsort(-scores)[:top_k * 3]
        # 主题锚定（与生产一致）
        anchor = None
        if len(query) > 15:
            try:
                anchor = self.vkb._get_anchor_query(query)
            except Exception:
                anchor = None
        if anchor:
            qa = self.vkb._get_query_embedding(anchor)
            sa = data['matrix'] @ qa
            anchor_idx = np.argsort(-sa)[:2]
            top_idx = np.concatenate([anchor_idx, top_idx])
        seen, results = set(), []
        for i in top_idx:
            aid = data['aids'][i]
            if aid in seen:
                continue
            seen.add(aid)
            results.append({
                'id': data['ids'][i], 'distance': float(-scores[i]),
                'metadata': data['metas'][i], 'text': data['docs'][i], 'aid': aid,
            })
            if len(results) >= top_k * 2:
                break
        hit_aids = list(dict.fromkeys(r['aid'] for r in results[:10]))
        graph = self.dg.build()
        skel = self.dg.skeleton(graph, hit_aids, top=skeleton_k)
        # 骨架块（从命中文章里挑对应文章）
        for sk in skel:
            for r in results:
                if r['aid'] == sk:
                    r['_skeleton'] = True
                    break
        return results, skel

def build_inject(results, skeleton, per=900):
    blocks, stats = [], []
    for r in results[:8]:
        meta = r.get('metadata', {})
        aid = meta.get('article_id', '?')
        text = r.get('text', '')
        if r.get('_skeleton'):
            header = f"[引用图骨架:{r['aid']}]"
        else:
            header = f"[{aid} @{meta.get('start','?')}-{meta.get('end','?')} dist:{r.get('distance',0):.3f}]"
        blocks.append(header + text[:per])
        stats.append({'article': aid, 'skeleton': bool(r.get('_skeleton')), 'chars': min(len(text), per)})
    return "\n\n".join(blocks), stats

# ---------- 完整性检查 ----------
def check_integrity(text, article_ids):
    refs = set()
    for m in re.finditer(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])', text):
        refs.add(f"{m.group(1)}.{m.group(2)}")
    dangling = sorted(refs - article_ids)
    gaps = []
    for m in re.finditer(r'【未验证】|【缺口】|来源未确认|无法提供来源|无可靠来源', text):
        start = max(0, m.start() - 70)
        end = min(len(text), m.end() + 70)
        gaps.append(re.sub(r'\s+', ' ', text[start:end]))
    return {'refs': sorted(refs), 'dangling': dangling, 'gaps': gaps}

# ---------- 主流程 ----------
TASK = """请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：
从 δ（基础间隙）出发，给出到达 α⁻¹ = 137.036 的完整推导链条。
要求：
1. 链条每一步说明机制（输入→操作→输出）
2. 每一步标注来源文章编号（如 2.6、1.5、0.8）
3. 给出关键公式（如 S(σ*) 的显式形式）
4. 如果某一步没有可靠来源，明确标注【未验证】
请以"推导链"形式输出，从 δ 开始到 137.036 结束。"""

SYS_BASE = "你是严格基于几何论文章库回答问题的共扼谱几何专家。所有结论必须可追溯，宁缺毋滥。"

def call_llm(client, sys_prompt, messages, max_tokens=4000):
    resp = client.chat.completions.create(
        model=GAI_MODEL_LITE,
        messages=[{"role": "system", "content": sys_prompt}] + messages,
        temperature=0.3,
        max_tokens=max_tokens,
        extra_body={'thinking': {'type': 'disabled'}},
    )
    return resp.choices[0].message.content or ''

def main():
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    from openai import OpenAI

    articles_dir = os.path.join(ROOT, 'app', 'articles')
    t0 = time.time()
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()
    dg = DynamicGraph(articles_dir)
    rt = DynamicRetriever(vkb, dg)
    print(f"[init] {time.time()-t0:.1f}s")

    # 摘要地图
    t0 = time.time()
    summary_lines = extract_summaries(articles_dir)
    summary_map = '\n'.join(summary_lines)
    print(f"[摘要地图] {len(summary_lines)} 篇, {len(summary_map)} 字符, {time.time()-t0:.1f}s")

    client = OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)

    # ---- Round 1 ----
    t0 = time.time()
    results, skel = rt.search(TASK, top_k=8)
    inject, stats = build_inject(results, skel)
    print(f"[R1 检索] {time.time()-t0:.2f}s, 命中 {len(results)} 块, 骨架 {skel}")
    for s in stats:
        tag = '骨架' if s['skeleton'] else '检索'
        print(f"   [{tag}] {s['article']} {s['chars']}字符")

    sys_prompt = SYS_BASE + "\n\n【文章地图（全部文章概览，用于定位来源，必须用编号引用）】\n" + summary_map + "\n\n【参考资料（当前轮检索结果，必须优先使用并标注来源）】\n" + inject
    messages = [{"role": "user", "content": TASK}]
    t0 = time.time()
    output = call_llm(client, sys_prompt, messages)
    print(f"[R1 生成] {time.time()-t0:.1f}s, {len(output)} 字符")

    report = check_integrity(output, dg.article_ids)
    print(f"[检查] 引用 {len(report['refs'])} 个, 悬空 {report['dangling']}, 缺口 {len(report['gaps'])} 处")
    for g in report['gaps']:
        print(f"   缺口: …{g}…")

    # ---- Round 2+：缺口驱动补检 ----
    rounds = 2
    while report['gaps'] and rounds <= 3:
        extra_blocks = []
        for gap in report['gaps'][:3]:
            q = gap.strip()
            if len(q) < 8:
                continue
            r2, _ = rt.search(q, top_k=4, skeleton_k=1)
            for r in r2[:3]:
                meta = r.get('metadata', {})
                aid = meta.get('article_id', '?')
                extra_blocks.append(f"[补检:{q[:40]} → {aid}]" + r.get('text', '')[:700])
        if not extra_blocks:
            break
        extra = "\n\n".join(extra_blocks)
        messages.append({"role": "assistant", "content": output})
        messages.append({"role": "user", "content": "【补充资料（针对缺口环节的新检索结果）】\n" + extra + "\n\n请基于补充资料修正推导链：对标注【未验证】的环节，若有来源则补全来源；若确实无来源，保留标注。只输出修正后的完整链条。"})
        t0 = time.time()
        output = call_llm(client, sys_prompt, messages)
        print(f"[R{rounds} 生成] {time.time()-t0:.1f}s, {len(output)} 字符")
        report = check_integrity(output, dg.article_ids)
        print(f"[检查] 引用 {len(report['refs'])} 个, 悬空 {report['dangling']}, 缺口 {len(report['gaps'])} 处")
        rounds += 1

    # ---- 保存 ----
    out = {
        'task': TASK,
        'rounds': rounds - 1,
        'final_output': output,
        'integrity': report,
        'summary_map_chars': len(summary_map),
        'inject_stats': stats,
        'skeleton': skel,
    }
    with open(os.path.join(ROOT, 'tools', 'iterative_result.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n完成: {rounds-1} 轮, 悬空引用 {len(report['dangling'])} 个, 缺口 {len(report['gaps'])} 处")
    print("结果已保存: tools/iterative_result.json")

if __name__ == '__main__':
    main()
