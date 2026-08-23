#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace 核心（供多任务压力测试复用）：
- 中间层：全量 embedding 矩阵/摘要地图/动态引用图/检索缓存 LRU 常驻内存
- 动态摘要子集：只注入检索命中 + 骨架 + 引用邻居的摘要
- 压缩注入：公式/定理/数值行优先，叙述丢弃
- 完整性检查：悬空引用 + 【未验证】缺口
- 推导状态机：链条/缺口/轮次在内存管理
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
        self.hits = 0
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
            if aid in seen or not re.match(r'^\d{1,2}\.\d{1,2}$', aid):
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
            cnt = graph.get(a)
            if cnt:
                for dst, _ in cnt.most_common(3):
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
        numeric = set()
        for m in re.finditer(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])', text):
            x, y = m.group(1), m.group(2)
            ref = f"{x}.{y}"
            # 过滤1：前导零（2.06 是数值）
            if y.startswith('0'):
                numeric.add(ref)
                continue
            # 过滤2：编号域外（X>12 或 Y>45 不可能是文章编号）
            if int(x) > 12 or int(y) > 45:
                numeric.add(ref)
                continue
            # 过滤3：上下文（前 12 字符有数学符号/数字且无引用词 → 数值）
            before = text[max(0, m.start() - 12):m.start()]
            if re.search(r'[=≈×±/<>（(\d]', before) and not re.search(r'文章|详见|参见|参考|定理|引理|命题|推论|公理|见|章|节|附录', before):
                numeric.add(ref)
                continue
            refs.add(ref)
        dangling = sorted(refs - self._article_ids)
        refs_all = sorted(refs | numeric)
        gaps = []
        for m in re.finditer(r'【未验证】|【缺口】|来源未确认|无法提供来源|无可靠来源', text):
            start = max(0, m.start() - 70)
            end = min(len(text), m.end() + 70)
            gaps.append(re.sub(r'\s+', ' ', text[start:end]))
        return {'refs': refs_all, 'dangling': dangling, 'numeric': sorted(numeric), 'gaps': gaps}

# ---------- 推导状态机 ----------
class ReasoningState:
    """推导状态：链条/缺口/轮次，全内存管理"""
    def __init__(self, task):
        self.task = task
        self.round = 0
        self.output = ''
        self.gaps = []
        self.dangling = []
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.rounds_info = []
        self.knowledge_gap = False

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

def run_task(ws, client, task_text, task_id, max_rounds=3):
    """完整推导任务：R1 检索生成 → 缺口驱动补检 → 返回结果 dict"""
    state = ReasoningState(task_text)

    # ---- Round 1 ----
    t0 = time.time()
    results, skel = ws.search(task_text, top_k=8)
    inject, stats = ws.build_inject(results, skel)
    hit_aids = list(dict.fromkeys(r['aid'] for r in results))
    summaries = ws.summaries_for(hit_aids + skel, max_chars=1400)
    t_retrieval = time.time() - t0

    sys_prompt = SYS_BASE + "\n\n【相关文章摘要（仅与推导相关的文章，用于定位来源，必须用编号引用）】\n" \
                 + summaries + "\n\n【参考资料（当前轮检索结果，压缩格式，必须优先使用并标注来源）】\n" + inject
    messages = [{"role": "user", "content": task_text}]
    t0 = time.time()
    output, usage = call_llm(client, sys_prompt, messages)
    report = ws.check_integrity(output)
    state.record_round('R1', output, usage, len(inject), len(summaries))
    t_gen = time.time() - t0

    # ---- Round 2+：缺口驱动补检（无进展即停） ----
    prev_gap_n = len(report['gaps'])
    while report['gaps'] and state.round < max_rounds:
        extra_blocks = []
        for gap in report['gaps'][:3]:
            q = gap.strip()
            if len(q) < 8:
                continue
            r2, sk2 = ws.search(q, top_k=4, skeleton_k=1)
            for r in r2[:3]:
                aid = r.get('metadata', {}).get('article_id', '?')
                extra_blocks.append(f"[补检:{q[:40]} → {aid}]" + ws.compress_block(r.get('text', ''), max_chars=400))
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
        t_gen += time.time() - t0
        # 无进展：缺口数未减少 → 判定为知识缺口（库中无闭合链条），停止补检
        if len(report['gaps']) >= prev_gap_n:
            state.knowledge_gap = True
            break
        prev_gap_n = len(report['gaps'])

    return {
        'task_id': task_id,
        'rounds': state.round,
        'final_output': output,
        'integrity': report,
        'token_total': state.prompt_tokens + state.completion_tokens,
        'prompt_tokens': state.prompt_tokens,
        'completion_tokens': state.completion_tokens,
        'rounds_info': state.rounds_info,
        'inject_stats': stats,
        'skeleton': skel,
        'hit_aids': hit_aids,
        't_retrieval_s': round(t_retrieval, 2),
        't_generation_s': round(t_gen, 1),
        'summary_chars': len(summaries),
        'summary_map_total_chars': sum(len(x) for x in ws._summaries.values()),
        'knowledge_gap': getattr(state, 'knowledge_gap', False),
    }
