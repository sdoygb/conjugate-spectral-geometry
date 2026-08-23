#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A/B 实验：动态关系管线 vs 静态管线
对比：注入质量（链条覆盖）+ 延迟

静态管线：vkb.search（HNSW+BM25+RRF+rerank 闸门）+ enrich_with_graph（静态引用图 JSON）
动态管线：全量暴力向量检索 + 动态引用提取（每次构建/进程内 mtime 缓存）+ 动态骨架
"""
import os, re, json, time, glob, sys
import numpy as np
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'app'))
ARTICLES_DIR = os.path.join(ROOT, 'app', 'articles')

TASK = """请完整推导精细结构常数 α⁻¹ = 137.036 的几何来源：
从 δ（基础间隙）出发，给出到达 α⁻¹ = 137.036 的完整推导链条。
要求：
1. 链条每一步说明机制（输入→操作→输出）
2. 每一步标注来源文章编号（如 2.6、1.5、0.8）
3. 给出关键公式（如 S(σ*) 的显式形式）
4. 如果某一步没有可靠来源，明确标注【未验证】
请以"推导链"形式输出，从 δ 开始到 137.036 结束。"""

# ---------- 动态引用提取（复用 build_citation_graph 的正则逻辑） ----------
pat_xyz = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})\.(\d{1,2})(?![0-9.])')
pat_xy = re.compile(r'(?<![0-9.])(\d{1,2})\.(\d{1,2})(?![0-9.])')
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


class DynamicGraph:
    """动态引用图：无持久化文件。构建时扫全库；进程内 mtime 变更检测缓存。"""

    def __init__(self, articles_dir, use_cache=True):
        self.articles_dir = articles_dir
        self.use_cache = use_cache
        self._cache = None
        self._mtime_sig = None

    def _scan(self):
        files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
        article_ids, id_to_file = set(), {}
        for f in files:
            base = os.path.basename(f)
            m = re.match(r'^(\d{1,2})\.(\d{1,2})', base)
            if m:
                aid = f"{m.group(1)}.{m.group(2)}"
                article_ids.add(aid)
                id_to_file[aid] = f
        graph = defaultdict(Counter)
        for aid, f in id_to_file.items():
            raw = open(f, encoding='utf-8').read()
            text = strip_toc(strip_math(raw))
            consumed = set()
            for m in pat_xyz.finditer(text):
                ref_xy = f"{m.group(1)}.{m.group(2)}"
                if ref_xy == aid or ref_xy not in article_ids:
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
                graph[aid][ref_xy] += 1
                consumed.add((m.start(), m.end()))
            for m in pat_xy.finditer(text):
                if any(s <= m.start() < e for s, e in consumed):
                    continue
                ref = f"{m.group(1)}.{m.group(2)}"
                if ref == aid or ref not in article_ids:
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
        return graph

    def build(self):
        t0 = time.time()
        if self.use_cache:
            files = sorted(glob.glob(os.path.join(self.articles_dir, '*.md')))
            sig = tuple((f, os.path.getmtime(f)) for f in files)
            if sig == self._mtime_sig and self._cache is not None:
                return self._cache, time.time() - t0
            graph = self._scan()
            self._cache, self._mtime_sig = graph, sig
        else:
            graph = self._scan()
        return graph, time.time() - t0

    def skeleton(self, graph, aids, top=3):
        """从文章集合出发一跳扩展：出边计数 + 入边计数，返回最高枢纽文章"""
        out_cnt, in_cnt = Counter(), Counter()
        for a in aids:
            for dst, c in graph.get(a, {}).items():
                if dst not in aids:
                    out_cnt[dst] += c
        for src, dsts in graph.items():
            for dst, c in dsts.items():
                if dst in aids and src not in aids:
                    in_cnt[src] += c
        hub = out_cnt + in_cnt
        return hub.most_common(top)


def load_all_embeddings(vkb):
    """一次性加载全库 embeddings + metadata + 文本（进程内缓存）"""
    if not hasattr(load_all_embeddings, '_data'):
        got = vkb._safe_collection_call(
            'articles_collection', 'get',
            include=['embeddings', 'metadatas', 'documents'])
        embs = np.array(got.get('embeddings', []), dtype=np.float32)
        metas = got.get('metadatas', [])
        docs = got.get('documents', [])
        aids = []
        for m in metas:
            fname = m.get('article_id', '?') or '?'
            mm = re.match(r'^(\d{1,2})\.(\d{1,2})', fname)
            aids.append(f"{mm.group(1)}.{mm.group(2)}" if mm else fname)
        load_all_embeddings._data = {
            'matrix': embs, 'metas': metas, 'docs': docs, 'aids': aids,
        }
    return load_all_embeddings._data


def dynamic_pipeline(vkb, query, top_k=8, skeleton_k=3):
    """动态管线：暴力向量检索 + 动态引用骨架 + 融合注入"""
    t0 = time.time()
    # 1. 查询 embedding
    q_emb = vkb._get_query_embedding(query)
    # 2. 全量暴力检索
    data = load_all_embeddings(vkb)
    scores = data['matrix'] @ q_emb
    top_idx = np.argsort(-scores)[:top_k * 4]
    t_retr = time.time() - t0
    # 3. 动态引用骨架
    dg = DynamicGraph(ARTICLES_DIR)
    graph, t_scan = dg.build()
    hit_aids = set()
    for i in top_idx:
        a = data['aids'][i]
        if a != '?':
            hit_aids.add(a)
    t1 = time.time()
    hub = dg.skeleton(graph, hit_aids, top=skeleton_k)
    t_skel = time.time() - t1
    # 3.5 主题锚定（与静态管线同能力：_TERM_MAP 锚定词暴力检索）
    anchor_items = []
    if len(query) > 15:
        _anchor_q = vkb._get_anchor_query(query)
        if _anchor_q and _anchor_q != query:
            _anchor_vec = vkb._get_query_embedding(_anchor_q)
            if _anchor_vec is not None:
                _a_scores = data['matrix'] @ _anchor_vec
                _a_idx = np.argsort(-_a_scores)[:2]
                for _i in _a_idx:
                    _m, _doc = data['metas'][_i], data['docs'][_i]
                    _aid = data['aids'][_i]
                    anchor_items.append({
                        'aid': _aid, 'doc': _doc,
                        'dist': round(float(_a_scores[_i]), 3),
                        'label': f"[主题锚定] {_aid}",
                        'meta': _m,
                    })
    # 4. 融合：锚定 + 向量 top chunks（按距离）+ 骨架块
    inject, stats = [], []
    used = set()
    for it in anchor_items:
        inject.append(f"[{it['label']} dist:{it['dist']}]" + it['doc'][:900])
        stats.append({'article': it['aid'], 'dist': it['dist'], 'type': 'anchor'})
        used.add(it['aid'])
    for i in top_idx[:top_k]:
        meta, doc = data['metas'][i], data['docs'][i]
        aid = data['aids'][i]
        header = f"[{aid} @{meta.get('start', '?')}-{meta.get('end', '?')} dist:{scores[i]:.3f}]"
        inject.append(header + doc[:900])
        stats.append({'article': aid, 'dist': round(float(scores[i]), 3), 'type': 'vec'})
        used.add(aid)
    # 骨架块：从引用图枢纽文章取对应 chunk（就近取该文章的一个 chunk）
    all_by_aid = defaultdict(list)
    for i, a in enumerate(data['aids']):
        all_by_aid[a].append(i)
    for aid, cnt in hub:
        if aid in used or aid not in all_by_aid:
            continue
        if not re.match(r'^\d{1,2}\.\d{1,2}$', aid):
            continue
        i = all_by_aid[aid][0]
        doc = data['docs'][i]
        inject.append(f"[引用图骨架:{aid}({cnt}次)]" + doc[:900])
        stats.append({'article': aid, 'hub': cnt, 'type': 'skeleton'})
    t_total = time.time() - t0
    if anchor_items:
        print(f"  主题锚定: {[it['aid'] for it in anchor_items]}")
    return '\n\n'.join(inject), stats, {
        'retrieval_ms': t_retr * 1000, 'scan_ms': t_scan * 1000,
        'skeleton_ms': t_skel * 1000, 'total_ms': t_total * 1000,
        'hit_articles': len(hit_aids), 'skeleton': hub,
    }


def static_pipeline(vkb, query, top_k=8):
    """静态管线：search + enrich（生产路径）"""
    t0 = time.time()
    results = vkb.search(query, top_k=top_k)
    t_search = time.time() - t0
    t0 = time.time()
    enhanced, labels = vkb.enrich_with_graph(results, query)
    t_enrich = time.time() - t0
    inject, stats = [], []
    for r in enhanced[:top_k + 3]:
        meta = r.get('metadata', {})
        aid = meta.get('article_id', '?')
        text = r.get('text', '')
        if r.get('label'):
            header = f"[{r['label']}]"
        else:
            header = f"[{aid} @{meta.get('start', '?')}-{meta.get('end', '?')} dist:{r.get('distance', 0):.3f}]"
        inject.append(header + text[:900])
        mm = re.match(r'^(\d{1,2})\.(\d{1,2})', aid)
        aid_num = f"{mm.group(1)}.{mm.group(2)}" if mm else aid
        stats.append({'article': aid_num, 'label': r.get('label', ''), 'type': 'skeleton' if r.get('label') else 'vec'})
    return '\n\n'.join(inject), stats, {
        'search_ms': t_search * 1000, 'enrich_ms': t_enrich * 1000,
        'labels': labels,
    }


CHAIN_ARTICLES = ['0.1', '0.8', '1.5', '2.4', '2.6', '5.5', '7.5', '9.6', '10.19', '10.39', '11.13', '11.14']


def main():
    from knowledge import VectorKnowledgeBase
    from config import CHROMA_DB_DIR
    vkb = VectorKnowledgeBase(CHROMA_DB_DIR)
    vkb.initialize()

    print("=" * 60)
    print("A/B 实验：动态管线 vs 静态管线（任务：137.036 推导链）")
    print("=" * 60)

    # ---- 静态 ----
    print("\n[静态管线] search + enrich_with_graph（生产路径）...")
    print("  预热 BM25（静态冷启动成本 12.6s 单独记录，不污染对比）...")
    t_warm0 = time.time()
    try:
        vkb.search("预热 137.036", top_k=1)
    except Exception:
        pass
    print(f"  BM25 冷启动: {(time.time()-t_warm0)*1000:.0f}ms")
    s_inject, s_stats, s_timing = static_pipeline(vkb, TASK)
    s_articles = {x['article'] for x in s_stats}
    print(f"  延迟: search={s_timing['search_ms']:.1f}ms enrich={s_timing['enrich_ms']:.1f}ms")
    print(f"  注入 {len(s_stats)} 块, 文章 {len(s_articles)} 篇:")
    for x in s_stats:
        print(f"    {x['type']:9s} {x['article']:8s} {x.get('label', x.get('dist', ''))}")
    s_cover = [a for a in CHAIN_ARTICLES if a in s_articles]
    print(f"  链条文章覆盖: {len(s_cover)}/{len(CHAIN_ARTICLES)}: {s_cover}")

    # ---- 动态 ----
    print("\n[动态管线] 暴力检索 + 动态引用提取 + 动态骨架...")
    d_inject, d_stats, d_timing = dynamic_pipeline(vkb, TASK)
    d_articles = {x['article'] for x in d_stats}
    print(f"  延迟: 检索={d_timing['retrieval_ms']:.1f}ms 引用扫描={d_timing['scan_ms']:.1f}ms "
          f"骨架={d_timing['skeleton_ms']:.1f}ms 总={d_timing['total_ms']:.1f}ms")
    print(f"  命中文章 {d_timing['hit_articles']} 篇, 动态骨架: {d_timing['skeleton']}")
    print(f"  注入 {len(d_stats)} 块, 文章 {len(d_articles)} 篇:")
    for x in d_stats:
        print(f"    {x['type']:9s} {x['article']:8s} {x.get('hub', x.get('dist', ''))}")
    d_cover = [a for a in CHAIN_ARTICLES if a in d_articles]
    print(f"  链条文章覆盖: {len(d_cover)}/{len(CHAIN_ARTICLES)}: {d_cover}")

    # ---- 对比 ----
    print("\n" + "=" * 60)
    print("对比汇总")
    print("=" * 60)
    print(f"  静态: 注入{len(s_stats)}块/{len(s_articles)}篇, 链条覆盖 {len(s_cover)}/{len(CHAIN_ARTICLES)}")
    print(f"  动态: 注入{len(d_stats)}块/{len(d_articles)}篇, 链条覆盖 {len(d_cover)}/{len(CHAIN_ARTICLES)}")
    print(f"  静态总延迟: {s_timing['search_ms'] + s_timing['enrich_ms']:.1f}ms")
    print(f"  动态总延迟: {d_timing['total_ms']:.1f}ms")
    only_d = [a for a in CHAIN_ARTICLES if a in d_articles and a not in s_articles]
    only_s = [a for a in CHAIN_ARTICLES if a in s_articles and a not in d_articles]
    print(f"  动态独有: {only_d}")
    print(f"  静态独有: {only_s}")

    # 保存
    out = {
        'static': {'stats': s_stats, 'timing': s_timing, 'cover': s_cover},
        'dynamic': {'stats': d_stats, 'timing': d_timing, 'cover': d_cover},
        'chain_articles': CHAIN_ARTICLES,
    }
    with open(os.path.join(ROOT, 'tools', 'verify_dynamic_vs_static.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n已保存: tools/verify_dynamic_vs_static.json")


if __name__ == '__main__':
    main()
