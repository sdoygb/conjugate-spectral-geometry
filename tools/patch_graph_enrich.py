#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 knowledge.py 添加引用图骨架增强方法，给 server.py 添加集成调用。"""
import io, sys

# ---------- 1. knowledge.py ----------
kp = 'app/knowledge.py'
src = io.open(kp, encoding='utf-8').read()

anchor = '''        return "\\n".join(contents), loaded_chunks

    def learn(self, q: str, a: str, score: float) -> bool:'''

assert src.count(anchor) == 1, f"knowledge anchor count={src.count(anchor)}"

new_methods = '''        return "\\n".join(contents), loaded_chunks

    # ---- 引用图骨架增强（推导类任务） ----
    _CITATION_GRAPH_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'tools', 'citation_graph.json')

    def _load_citation_graph(self) -> dict:
        """懒加载引用图（tools/citation_graph.json）。失败返回空 dict。"""
        if not hasattr(self, '_graph_cache'):
            self._graph_cache = None
        if self._graph_cache is None:
            try:
                with open(self._CITATION_GRAPH_PATH, encoding='utf-8') as f:
                    self._graph_cache = json.load(f)
                logger.info(
                    f"[GRAPH] 引用图加载: "
                    f"{self._graph_cache.get('meta', {}).get('edges', 0)} 条边")
            except Exception as e:
                logger.debug(f"[GRAPH] 引用图加载失败: {e}")
                self._graph_cache = {}
        return self._graph_cache

    def enrich_with_graph(self, results: List[Dict[str, Any]], query: str,
                          max_skeleton: int = 3,
                          chunks_per_article: int = 1) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        引用图骨架增强：推导类任务专用。
        1. 从检索结果提取入口文章编号（fname 前缀）
        2. 沿引用图 out+in 扩展骨架文章（按引用次数降序，排除入口）
        3. 从 ChromaDB 按 fname 过滤拉取骨架文章与该查询最相关的 chunk
        4. 骨架 chunk 标记 _skeleton=True 插到结果最前
        返回 (增强后结果, 骨架标签列表)
        """
        try:
            graph = self._load_citation_graph()
            if not graph or not results:
                return results, []

            # 1. 入口编号（fname 前缀，如 "1.5_代数作用量S(σ)_CN_260808.md" -> "1.5"）
            entry_ids = set()
            for r in results:
                fname = r.get('metadata', {}).get('fname', '') or ''
                _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
                if _m:
                    entry_ids.add(_m.group(1))
            if not entry_ids:
                return results, []

            # 2. 骨架扩展：out + in 邻居，按引用次数聚合排序
            out_map = graph.get('out', {})
            in_map = graph.get('in', {})
            neigh: Dict[str, int] = {}
            for eid in entry_ids:
                for _m in (out_map.get(eid, {}), in_map.get(eid, {})):
                    for nid, info in _m.items():
                        neigh[nid] = neigh.get(nid, 0) + info.get('count', 1)
            skeleton = sorted(
                ((nid, c) for nid, c in neigh.items() if nid not in entry_ids),
                key=lambda x: -x[1]
            )[:max_skeleton]
            if not skeleton:
                return results, []

            # 3. 编号 -> 文件名映射（从文章目录扫描）
            id_to_fname = {}
            try:
                for fname in os.listdir(self._articles_dir):
                    _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
                    if _m:
                        id_to_fname.setdefault(_m.group(1), fname)
            except Exception:
                pass

            _qvec = self._get_query_embedding(query)
            new_chunks = []
            for nid, cnt in skeleton:
                fname = id_to_fname.get(nid)
                if not fname:
                    continue
                try:
                    if _qvec:
                        sub = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_embeddings=[_qvec],
                            n_results=chunks_per_article,
                            where={"fname": fname}
                        )
                    else:
                        sub = self._safe_collection_call(
                            'articles_collection', 'query',
                            query_texts=[query],
                            n_results=chunks_per_article,
                            where={"fname": fname}
                        )
                    if sub and sub['documents']:
                        for i, doc in enumerate(sub['documents'][0]):
                            meta = sub['metadatas'][0][i] if sub['metadatas'] else {}
                            dist = sub['distances'][0][i] if sub['distances'] else 0.0
                            new_chunks.append({
                                'id': meta.get('chunk_id', ''),
                                'text': doc,
                                'source': 'articles',
                                'metadata': meta,
                                'distance': dist,
                                '_skeleton': True,
                                'label': f"[引用图骨架:{nid}({cnt}次)] 文章库: {fname}"
                            })
                except Exception as e:
                    logger.debug(f"[GRAPH] 骨架文章 {nid} 拉取失败: {e}")

            if not new_chunks:
                return results, []

            # 4. 合并：骨架优先，去重
            existing_ids = set()
            for r in results:
                cid = r.get('id') or r.get('metadata', {}).get('chunk_id', '')
                if cid:
                    existing_ids.add(cid)
            skeleton_chunks = [c for c in new_chunks if (c.get('id') or '') not in existing_ids]
            merged = skeleton_chunks + results
            return merged, [c['label'] for c in skeleton_chunks]
        except Exception as e:
            logger.error(f"[GRAPH] 引用图增强失败: {e}")
            return results, []

    def learn(self, q: str, a: str, score: float) -> bool:'''

src = src.replace(anchor, new_methods)
io.open(kp, 'w', encoding='utf-8').write(src)
print(f"[OK] knowledge.py 已添加 enrich_with_graph")

# ---------- 2. server.py ----------
sp = 'app/server.py'
src2 = io.open(sp, encoding='utf-8').read()

anchor2 = '''            merged.sort(key=lambda x: x.get('distance', 1.0))
            results = merged[:MAX_CHUNKS_PER_QUERY]'''

assert src2.count(anchor2) == 1, f"server anchor count={src2.count(anchor2)}"

repl2 = '''            merged.sort(key=lambda x: (1 if x.get('_skeleton') else 0,
                                       x.get('distance', 1.0)))
            # 推导类任务：引用图骨架增强（骨架文章 chunk 插到最前）
            _deriv_pat = re.compile(r'推导|证明|机制|来源|链条|如何|为什么|得出|导出|验证|完整')
            if _deriv_pat.search(clean_query) and merged:
                merged, _gchunks = vector_kb.enrich_with_graph(merged, search_query)
                if _gchunks:
                    logger.info(f"[VECTOR-GRAPH] 引用图骨架注入: {len(_gchunks)} 块")
            results = merged[:MAX_CHUNKS_PER_QUERY]'''

src2 = src2.replace(anchor2, repl2)
io.open(sp, 'w', encoding='utf-8').write(src2)
print(f"[OK] server.py 已集成引用图骨架增强")
