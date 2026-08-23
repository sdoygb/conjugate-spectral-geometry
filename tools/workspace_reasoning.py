#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace 中间层 + 迭代检索 v2：中间产物全内存，token 最小化
- 中间层：全量 embedding 矩阵/文章文本/摘要地图/动态引用图/检索缓存 LRU 常驻内存
- 动态摘要子集：只注入检索命中 + 骨架 + 引用邻居的摘要（~1.4K 字符），不注入全量
- 压缩注入：块级压缩（公式/定理/数值行优先，叙述丢弃）
- 推导状态机：链条/缺口/已注入文章/轮次在内存管理
- 完整性检查：悬空引用 + 【未验证】缺口，缺口驱动补检
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

def strip_math(text):
    text = re.sub(r'\$[^$]*\$', ' ', text)
    text = re.sub(r'\\\(.*?\\\)', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', ' ', text, flags=re.DOTALL)
    return text

def strip_toc(text):
    return re.sub(r'##\s*目\s*录.*?(?=\n##|\n---|\Z)', '', text, flags=re.DOTALL)

# ---------- Workspace 中间层 ----------
class Workspace:
    """中间层：全量数据常驻内存，中间产物不落盘，检索缓存 LRU"""

    def __init__(self, vkb, articles_dir, cache_max=50):
        self.vkb = vkb
        self.articles_dir = articles_dir
        self.cache_max = cache_max
        self._data = None            # 全量 embeddings + meta + docs + aids
        self._summaries = None       # {aid: 摘要}
        self._graph = None           # 动态引用图 {aid: Counter}
        self._article_ids = set()
        self._sig = None             # 文章 mtime 签名
        self._cache = {}             # query_hash -> (results, skel)
        self._cache_order = []
        self.hits = 0                # 缓存命中计数
        self.misses = 0

    # ---- 加载（一次性） ----
    def load_all(self):
        t0 = time.time()
        if self._data is None:
            col = self.vkb.articles_collection
            got = col.get(include=['embeddings', 'metadatas', 'documents'])
            embs = np.array(got['embeddings'], dtype=np.float32)
            aids = []
            for meta in got['metadatas']:
                fn = meta.get('article_id', '?')
                mm = re.match(r'^(\d{1,2})\.(\d{1,2})', fn)
                aids.append(f"{mm.group(1)}.{mm.group(2)}" if mm else fn)
            self._data = {'ids': got['ids'], 'matrix': embs,
                          'metas': got['metadatas'], 'docs': got['documents'],
                          'aids': aids}
        if self._summaries is None:
            self._summaries = self._extract_summaries()
        self.build_graph()
        return time.time() - t0

    # ---- 摘要地图（内存 dict，不注入全量） ----
    def _extract_summaries(self):
        out = {}
        files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
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
            if len(abs_text) > 120:
                abs_text = abs_text[:120] + '…'
            out[aid] = f"{aid} {title}：{abs_text}"
        return out

    # ---- 动态引用图（mtime 自动失效） ----
    def build_graph(self):
        files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
        sig = tuple((f, os.path.getmtime(f)) for f in files)
        if sig == self._sig and self._graph is not None:
            return self._graph
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
        self._graph, self._article_ids, self._sig = graph, ids, sig
        return graph

    def skeleton(self, hit_aids, top=3):
        graph = self.build_graph()
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

    # ---- 检索（缓存 LRU） ----
    @staticmethod
    def _norm_query(q):
        return re.sub(r'\s+', '', q)

    def search(self, query, top_k=8, skeleton_k=3):
        key = self._norm_query(query)
        if key in self._cache:
            self._cache_order.remove(key)
            self._cache_order.append(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        data = self._data
        q = self.vkb._get_query_embedding(query)
        scores = data['matrix'] @ q
        top_idx = np.argsort(-scores)[:top_k * 3]
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
        skel = self.skeleton(hit_aids, top=skeleton_k)
        for sk in skel:
            for r in results:
                if r['aid'] == sk:
                    r['_skeleton'] = True
                    break
        self._cache[key] = (results, skel)
        self._cache_order.append(key)
        if len(self._cache_order) > self.cache_max:
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)
        return results, skel

    # ---- 动态摘要子集（只注入相关的） ----
    def summaries_for(self, aids, max_chars=1400):
        graph = self.build_graph()
        extra = set()
        for a in list(aids)[:6]:
            for dst, _ in graph.get(a, {}).most_common(3):
                extra.add(dst)
        all_aids = list(dict.fromkeys(list(aids) + sorted(extra)))
        lines, total = [], 0
        for a in all_aids:
            s = self._summaries.get(a)
            if not s:
                continue
            lines.append(s)
            total += len(s) + 1
            if total > max_chars:
                break
        return '\n'.join(lines)

    # ---- 压缩注入（公式/定理/数值行优先） ----
    @staticmethod
    def compress_block(text, max_chars=500):
        lines = text.split('\n')
        high, normal = [], []
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if ('$' in s or re.match(r'^(定理|命题|定义|推论|引理|注|公理|假设|性质)', s)
                    or re.search(r'[σδαλξηψΩΛ]', s) or re.search(r'\d+\.\d+', s)):
                high.append(s)
            else:
                normal.append(s)
        out, total = [], 0
        for s in high + normal:
            if total >= max_chars:
                break
            out.append(s)
            total += len(s) + 1
        return '\n'.join(out)

    def build_inject(self, results, skeleton, per=500):
        blocks, stats = [], []
        for r in results[:8]:
            meta = r.get('metadata', {})
            aid = meta.get('article_id', '?')
            text = r.get('text', '')
            if r.get('_skeleton'):
                header = f"[引用图骨架:{r['aid']}]"
            else:
                header = f"[{aid} @{meta.get('start','?')}-{meta.get('end','?')} dist:{r.get('distance',0):.3f}]"
            comp = self.compress_block(text, max_chars=per)
            blocks.append(header + comp)
            stats.append({'article': aid, 'skeleton': bool(r.get('_skeleton')),
                          'chars': len(comp), 'raw_chars': len(text)})
        return "\n\n".join(blocks), stats

    # ---- 完整性检查 ----
    def check_integrity(self, text):
        refs = set()
        for m in re.finditer(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])', text):
            refs.add(f"{m.group(1)}.{m.group(2)}")
        dangling = sorted(refs - self._article_ids)
        gaps = []
        for m in re.finditer(r'【未验证】|【缺口】|来源未确认|无法提供来源|无可靠来源', text):
            start = max(0, m.start() - 70)
            end = min(len(text), m.end() + 70)
            gaps.append(re.sub(r'\s+', ' ', text[start:end]))
        return {'refs': sorted(refs), 'dangling': dangling, 'gaps': gaps}

# ---------- 推导状态机 ----------
class ReasoningState:
    """推导状态：链条/缺口/已注入文章/轮次，全内存管理"""
    def __init__(self, task):
        self.task = task
        self.round = 0
        self.output = ''
        self.gaps = []
        self.dangling = []
        self.injected_aids = set()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.rounds_info = []

    def record_round(self, label, output, usage, inject_chars, summary_chars):
        self.round += 1
        self.output = output
        if usage:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
        self.rounds_info.append({
            'round': self.round, 'label': label, 'out_chars': len(output),
            'inject_chars': inject_chars, 'summary_chars': summary_chars,
            'prompt_tokens': usage.prompt_tokens if usage else 0,
            'completion_tokens': usage.completion_tokens if usage else 0,
        })

# ---------- LLM ----------
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
    return resp.choices[0].message.content or '', resp.usage

def main():
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    from openai import OpenAI

    articles_dir = os.path.join(ROOT, 'app', 'articles')
    t0 = time.time()
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()
    ws = Workspace(vkb, articles_dir)
    load_t = ws.load_all()
    print(f"[init] {time.time()-t0:.1f}s (含全量加载 {load_t:.1f}s)")
    print(f"[中间层] embedding矩阵 {ws._data['matrix'].shape}, 摘要 {len(ws._summaries)} 篇, "
          f"引用图 {len(ws._graph)} 篇文章有出边")

    client = OpenAI(api_key=GAI_API_KEY, base_url=GAI_BASE_URL)
    state = ReasoningState(TASK)

    # ---- Round 1 ----
    t0 = time.time()
    results, skel = ws.search(TASK, top_k=8)
    inject, stats = ws.build_inject(results, skel)
    hit_aids = list(dict.fromkeys(r['aid'] for r in results))
    summaries = ws.summaries_for(hit_aids + skel, max_chars=1400)
    print(f"[R1 检索] {time.time()-t0:.2f}s, 命中 {len(results)} 块, 骨架 {skel}")
    print(f"[R1 注入] 检索 {len(inject)} 字符, 摘要子集 {len(summaries)} 字符 "
          f"(全量是 {sum(len(x) for x in ws._summaries.values())} 字符)")

    sys_prompt = SYS_BASE + "\n\n【相关文章摘要（仅与推导相关的文章，用于定位来源，必须用编号引用）】\n" \
                 + summaries + "\n\n【参考资料（当前轮检索结果，压缩格式，必须优先使用并标注来源）】\n" + inject
    messages = [{"role": "user", "content": TASK}]
    t0 = time.time()
    output, usage = call_llm(client, sys_prompt, messages)
    report = ws.check_integrity(output)
    state.record_round('R1', output, usage, len(inject), len(summaries))
    print(f"[R1 生成] {time.time()-t0:.1f}s, {len(output)} 字符, tokens in={usage.prompt_tokens} out={usage.completion_tokens}")
    print(f"[检查] 引用 {len(report['refs'])} 个, 悬空 {report['dangling']}, 缺口 {len(report['gaps'])} 处")

    # ---- Round 2+：缺口驱动补检 ----
    while report['gaps'] and state.round < 3:
        extra_blocks = []
        for gap in report['gaps'][:3]:
            q = gap.strip()
            if len(q) < 8:
                continue
            r2, sk2 = ws.search(q, top_k=4, skeleton_k=1)
            for r in r2[:3]:
                aid = r.get('metadata', {}).get('article_id', '?')
                extra_blocks.append(f"[补检:{q[:40]} → {aid}]" + ws.compress_block(r.get('text', ''), max_chars=400))
                state.injected_aids.add(r['aid'])
        if not extra_blocks:
            break
        extra = "\n\n".join(extra_blocks)
        messages.append({"role": "assistant", "content": output})
        messages.append({"role": "user", "content": "【补充资料（针对缺口环节的新检索结果，压缩格式）】\n" + extra
                         + "\n\n请基于补充资料修正推导链：对标注【未验证】的环节，若有来源则补全来源；若确实无来源，保留标注。只输出修正后的完整链条。"})
        t0 = time.time()
        output, usage = call_llm(client, sys_prompt, messages)
        report = ws.check_integrity(output)
        state.record_round(f'R{state.round+1}', output, usage, len(extra), 0)
        print(f"[R{state.round} 生成] {time.time()-t0:.1f}s, {len(output)} 字符, "
              f"tokens in={usage.prompt_tokens} out={usage.completion_tokens}")
        print(f"[检查] 引用 {len(report['refs'])} 个, 悬空 {report['dangling']}, 缺口 {len(report['gaps'])} 处")

    # ---- 报告（内存状态 → 记录文件） ----
    out = {
        'task': TASK,
        'rounds': state.round,
        'final_output': output,
        'integrity': report,
        'token_total': state.prompt_tokens + state.completion_tokens,
        'prompt_tokens': state.prompt_tokens,
        'completion_tokens': state.completion_tokens,
        'rounds_info': state.rounds_info,
        'cache': {'hits': ws.hits, 'misses': ws.misses},
        'inject_stats': stats,
        'skeleton': skel,
        'summary_map_total_chars': sum(len(x) for x in ws._summaries.values()),
    }
    with open(os.path.join(ROOT, 'tools', 'workspace_result.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n完成: {state.round} 轮, 总 tokens {state.prompt_tokens + state.completion_tokens} "
          f"(in={state.prompt_tokens}), 缓存命中 {ws.hits}/{ws.hits + ws.misses}")
    print("结果已保存: tools/workspace_result.json")

if __name__ == '__main__':
    main()
