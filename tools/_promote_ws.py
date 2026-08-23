# -*- coding: utf-8 -*-
"""Workspace 中间层转正：knowledge.py + config.py 精确替换（带断言）"""

WS_METHODS = '''
    def _workspace_init(self) -> bool:
        """初始化 Workspace 中间层：全量 embeddings + 文本 + 摘要地图 + 动态引用图。
        加速层：失败时 _use_workspace=False 自动回退旧路径（HNSW + 静态引用图）。"""
        if not self._use_workspace:
            return False
        if self._ws is not None:
            return True
        try:
            all_data = self._safe_collection_call(
                'articles_collection', 'get',
                include=['embeddings', 'documents', 'metadatas'])
            if not all_data or not all_data.get('ids'):
                logger.warning("[WS] 全量加载失败（空集合），回退旧路径")
                self._use_workspace = False
                return False
            emb = np.array(all_data['embeddings'], dtype=np.float32)
            norm = np.linalg.norm(emb, axis=1, keepdims=True)
            norm[norm == 0] = 1.0
            emb = emb / norm
            docs = all_data['documents'] or []
            metas = all_data['metadatas'] or [{}] * len(docs)
            aids = []
            for _m in metas:
                _fn = (_m or {}).get('fname', '')
                _mm = re.match(r'^(\\d{1,2})\\.(\\d{1,2})', _fn)
                aids.append(_mm.group(1) if _mm else '')
            self._ws = {
                'emb': emb, 'docs': docs, 'metas': metas, 'aids': aids,
                'summary_map': None, 'graph': None, 'sig': None,
            }
            self._workspace_scan_articles()
            logger.info(
                f"[WS] 中间层就绪: {emb.shape[0]} chunks x {emb.shape[1]} 维 | "
                f"摘要 {(self._ws.get('summary_map') or {}) and len(self._ws['summary_map'])} 篇 | "
                f"引用图 {(self._ws.get('graph') or {}) and len(self._ws['graph'])} 篇")
            return True
        except Exception as e:
            logger.warning(f"[WS] 中间层初始化失败，回退旧路径: {e}")
            self._use_workspace = False
            self._ws = None
            return False

    def _workspace_scan_articles(self):
        """扫描文章目录：构建摘要地图 + 动态引用图（内存，mtime 自动失效）。"""
        if not self._articles_dir or not os.path.isdir(self._articles_dir):
            return
        files = sorted(glob.glob(os.path.join(self._articles_dir, '*.md')))
        if not files:
            return
        sig = tuple((f, os.path.getmtime(f)) for f in files)
        ws = self._ws
        if ws.get('sig') == sig and ws.get('summary_map') is not None:
            return  # 无变更，复用内存结果
        _pat_xyz = re.compile(r'(?<![0-9.])(\\d{1,2})\\.(\\d{1,2})\\.(\\d{1,2})(?![0-9.])')
        _pat_xy = re.compile(r'(?<![0-9.])(\\d{1,2})\\.(\\d{1,2})(?![0-9.])')
        summaries, graph = {}, {}
        for f in files:
            base = os.path.basename(f)
            _m = re.match(r'^(\\d{1,2})\\.(\\d{1,2})_', base)
            if not _m:
                continue
            aid = f"{_m.group(1)}.{_m.group(2)}"
            try:
                raw = open(f, encoding='utf-8').read()
            except Exception:
                continue
            # 摘要（编号 + 标题 + 摘要首句，去公式）
            title = ''
            _tm = re.search(r'^#\\s+(.+)$', raw, re.M)
            if _tm:
                title = _tm.group(1).strip()
            _am = re.search(r'##\\s*摘要\\s*\\n+(.+?)(?:\\n\\n|\\n---|\\Z)', raw, re.DOTALL)
            _abs = ''
            if _am:
                _abs = re.sub(r'\\s+', ' ', _am.group(1)).strip()
                _abs = re.sub(r'\\$[^$]*\\$', '', _abs)
                if len(_abs) > 120:
                    _abs = _abs[:120] + '…'
            summaries[aid] = f"{aid} {title}：{_abs}" if title else f"{aid}：{_abs}"
            # 引用出边（去目录/公式，引用计数）
            text = re.sub(r'##\\s*目\\s*录.*?(?=\\n##|\\n---|\\Z)', '', raw, flags=re.DOTALL)
            text = re.sub(r'\\$[^$]*\\$', ' ', text)
            outs = {}
            consumed = set()
            for _mm in _pat_xyz.finditer(text):
                _ref = f"{_mm.group(1)}.{_mm.group(2)}"
                if _ref == aid:
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '\\u3000':
                    continue
                if _mm.start() > 0 and text[_mm.start() - 1] in '§#':
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '%':
                    continue
                outs[_ref] = outs.get(_ref, 0) + 1
                consumed.add((_mm.start(), _mm.end()))
            for _mm in _pat_xy.finditer(text):
                if any(_s <= _mm.start() < _e for _s, _e in consumed):
                    continue
                _ref = f"{_mm.group(1)}.{_mm.group(2)}"
                if _ref == aid:
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '\\u3000':
                    continue
                if _mm.start() > 0 and text[_mm.start() - 1] in '§#':
                    continue
                if _mm.end() < len(text) and text[_mm.end()] == '%':
                    continue
                outs[_ref] = outs.get(_ref, 0) + 1
            graph[aid] = outs
        ws['summary_map'] = summaries
        ws['graph'] = graph
        ws['sig'] = sig

    def _workspace_query_results(self, qvec, n) -> Optional[dict]:
        """暴力检索 top-n，返回 ChromaDB query 兼容格式 {'documents': [[..]], 'metadatas': [[..]], 'distances': [[..]]}。
        异常返回 None（上层回退 ChromaDB）。"""
        try:
            ws = self._ws
            if ws is None or qvec is None:
                return None
            q = np.asarray(qvec, dtype=np.float32)
            nq = np.linalg.norm(q)
            if nq > 0:
                q = q / nq
            sims = ws['emb'] @ q  # (N,) cosine 相似度
            top = np.argsort(-sims)[:n]
            docs, metas, dists = [], [], []
            for i in top:
                _m = ws['metas'][i] or {}
                docs.append(ws['docs'][i])
                metas.append(_m)
                dists.append(float(1.0 - sims[i]))
            return {'documents': [docs], 'metadatas': [metas], 'distances': [dists]}
        except Exception as e:
            logger.warning(f"[WS] 暴力检索异常: {e}")
            return None

    def _workspace_skeleton(self, entry_ids, max_skeleton=3):
        """动态引用图骨架：入口文章的 out(权重2) + in(权重1) 邻居计数，取 top。"""
        graph = self._ws.get('graph') or {}
        neigh = {}
        for eid in entry_ids:
            for nid, cnt in (graph.get(eid) or {}).items():
                neigh[nid] = neigh.get(nid, 0) + 2 * cnt
            for src, outs in graph.items():
                if eid in outs:
                    neigh[src] = neigh.get(src, 0) + outs[eid]
        skeleton = sorted(
            ((nid, c) for nid, c in neigh.items() if nid not in entry_ids),
            key=lambda x: -x[1])[:max_skeleton]
        return skeleton

    def _workspace_chunks_for(self, fname, qvec=None, chunks_per_article=1):
        """从内存全量 documents 按 fname 过滤，返回该文章 top 相关 chunk（骨架用）。"""
        ws = self._ws
        idxs = [i for i, _m in enumerate(ws['metas']) if (_m or {}).get('fname') == fname]
        if not idxs:
            return []
        if qvec is not None and len(idxs) > chunks_per_article:
            q = np.asarray(qvec, dtype=np.float32)
            nq = np.linalg.norm(q)
            if nq > 0:
                q = q / nq
            sims = ws['emb'][idxs] @ q
            order = np.argsort(-sims)[:chunks_per_article]
            idxs = [idxs[i] for i in order]
        else:
            idxs = idxs[:chunks_per_article]
        out = []
        for i in idxs:
            _m = ws['metas'][i] or {}
            out.append({
                'id': _m.get('chunk_id', ''),
                'text': ws['docs'][i],
                'source': 'articles',
                'metadata': _m,
                'distance': 0.0,
                '_skeleton': True,
                'label': f"[引用图骨架:{fname}] 文章库: {_m.get('fname', '未知')}"
            })
        return out

    def _enrich_with_workspace(self, results, query, max_skeleton=3, chunks_per_article=1):
        """Workspace 动态骨架增强：动态引用图（内存）+ 内存拉取骨架 chunk。"""
        if not results:
            return results, []
        entry_ids = set()
        for r in results:
            fname = r.get('metadata', {}).get('fname', '') or ''
            _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
            if _m:
                entry_ids.add(_m.group(1))
        if not entry_ids:
            return results, []
        skeleton = self._workspace_skeleton(entry_ids, max_skeleton)
        if not skeleton:
            return results, []
        id_to_fname = {}
        if self._articles_dir:
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
            for c in self._workspace_chunks_for(fname, _qvec, chunks_per_article):
                c['label'] = f"[引用图骨架:{nid}({cnt}次)] 文章库: {c.get('metadata', {}).get('fname', fname)}"
                new_chunks.append(c)
        if not new_chunks:
            return results, []
        existing_ids = set()
        for r in results:
            cid = r.get('id') or r.get('metadata', {}).get('chunk_id', '')
            if cid:
                existing_ids.add(cid)
        skeleton_chunks = [c for c in new_chunks if (c.get('id') or '') not in existing_ids]
        merged = skeleton_chunks + results
        return merged, [c['label'] for c in skeleton_chunks]

'''

def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        src = f.read()
    for old, new, tag in repls:
        n = src.count(old)
        assert n == 1, f"[{tag}] 锚点出现 {n} 次（期望 1）: {old[:60]!r}"
        src = src.replace(old, new)
        print(f"  OK [{tag}]")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f"  写入 {path}")

# ========== config.py ==========
patch('app/config.py', [
    (
        "EMBEDDING_MODE = os.getenv('GAI_EMBEDDING_MODE', 'siliconflow')",
        "EMBEDDING_MODE = os.getenv('GAI_EMBEDDING_MODE', 'siliconflow')\n"
        "# Workspace 中间层开关（转正：暴力检索 + 动态引用图；异常自动回退旧路径）\n"
        "USE_WORKSPACE = os.getenv('USE_WORKSPACE', '1') == '1'",
        "config: USE_WORKSPACE",
    ),
])

# ========== knowledge.py ==========
kn_repls = []
kn_repls.append((
    "import os\nimport re\nimport math\nimport hashlib\nimport time\nimport json\nimport threading",
    "import os\nimport re\nimport math\nimport hashlib\nimport time\nimport json\nimport threading\n"
    "import glob\nimport numpy as np",
    "import numpy/glob",
))
kn_repls.append((
    "    EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,\n    CHROMADB_AVAILABLE,",
    "    EMBEDDING_MODE, LOCAL_EMBEDDING_MODEL,\n    USE_WORKSPACE,\n    CHROMADB_AVAILABLE,",
    "import USE_WORKSPACE",
))
kn_repls.append((
    '        self._articles_dir = ""  # articles 目录路径',
    '        self._articles_dir = ""  # articles 目录路径\n'
    '        self._use_workspace = USE_WORKSPACE  # Workspace 中间层开关（转正）\n'
    '        self._ws = None  # 中间层：emb矩阵/docs/metas/aids/summary_map/graph/sig',
    "__init__ workspace 成员",
))
kn_repls.append((
    "            self._initialized = True\n"
    "            logger.info(\n"
    "                f\"[VECTOR] ChromaDB 初始化成功 | \"",
    "            self._initialized = True\n"
    "            # Workspace 中间层（加速层：暴力检索+动态图；失败自动回退旧路径）\n"
    "            try:\n"
    "                self._workspace_init()\n"
    "            except Exception as _wse:\n"
    "                logger.warning(f\"[WS] 中间层初始化异常（回退旧路径）: {_wse}\")\n"
    "                self._use_workspace = False\n"
    "            logger.info(\n"
    "                f\"[VECTOR] ChromaDB 初始化成功 | \"",
    "initialize 尾部挂载",
))
kn_repls.append((
    "    @property\n    def is_initialized(self) -> bool:\n        return self._initialized",
    WS_METHODS + "\n    @property\n    def is_initialized(self) -> bool:\n        return self._initialized",
    "插入 Workspace 方法组",
))
kn_repls.append((
    "                # 优先用缓存向量（query_embeddings），避免重复调用 embedding API\n"
    "                _qvec = self._get_query_embedding(query)\n"
    "                if _qvec:\n"
    "                    art_results = self._safe_collection_call(\n"
    "                        'articles_collection', 'query',\n"
    "                        query_embeddings=[_qvec],\n"
    "                        n_results=n_articles\n"
    "                    )\n"
    "                else:",
    "                # 优先用缓存向量（query_embeddings），避免重复调用 embedding API\n"
    "                _qvec = self._get_query_embedding(query)\n"
    "                if _qvec:\n"
    "                    if self._use_workspace and self._ws is not None:\n"
    "                        art_results = self._workspace_query_results(_qvec, n_articles)\n"
    "                        if art_results is None:\n"
    "                            # 中间层异常：回退 ChromaDB（只回退一次）\n"
    "                            logger.warning(\"[WS] 暴力检索异常，回退 ChromaDB 路径\")\n"
    "                            self._use_workspace = False\n"
    "                            art_results = self._safe_collection_call(\n"
    "                                'articles_collection', 'query',\n"
    "                                query_embeddings=[_qvec],\n"
    "                                n_results=n_articles\n"
    "                            )\n"
    "                    else:\n"
    "                        art_results = self._safe_collection_call(\n"
    "                            'articles_collection', 'query',\n"
    "                            query_embeddings=[_qvec],\n"
    "                            n_results=n_articles\n"
    "                        )\n"
    "                else:",
    "search 主检索分支",
))
kn_repls.append((
    "                        _anchor_vec = self._get_query_embedding(_anchor_q)\n"
    "                        if _anchor_vec:\n"
    "                            _anchor_res = self._safe_collection_call(\n"
    "                                'articles_collection', 'query',\n"
    "                                query_embeddings=[_anchor_vec],\n"
    "                                n_results=min(5, n_articles)\n"
    "                            )",
    "                        _anchor_vec = self._get_query_embedding(_anchor_q)\n"
    "                        if _anchor_vec:\n"
    "                            if self._use_workspace and self._ws is not None:\n"
    "                                _anchor_res = self._workspace_query_results(_anchor_vec, min(5, n_articles))\n"
    "                                if _anchor_res is None:\n"
    "                                    self._use_workspace = False\n"
    "                                    _anchor_res = self._safe_collection_call(\n"
    "                                        'articles_collection', 'query',\n"
    "                                        query_embeddings=[_anchor_vec],\n"
    "                                        n_results=min(5, n_articles)\n"
    "                                    )\n"
    "                            else:\n"
    "                                _anchor_res = self._safe_collection_call(\n"
    "                                    'articles_collection', 'query',\n"
    "                                    query_embeddings=[_anchor_vec],\n"
    "                                    n_results=min(5, n_articles)\n"
    "                                )",
    "search 锚定分支",
))
kn_repls.append((
    "        try:\n"
    "            graph = self._load_citation_graph()\n"
    "            if not graph or not results:\n"
    "                return results, []",
    "        # Workspace 模式：动态引用图（内存）+ 内存拉取骨架 chunk\n"
    "        if self._use_workspace and self._ws is not None and (self._ws.get('graph') or {}):\n"
    "            try:\n"
    "                return self._enrich_with_workspace(results, query, max_skeleton, chunks_per_article)\n"
    "            except Exception as _wse:\n"
    "                logger.warning(f\"[WS] 动态骨架异常（回退静态图）: {_wse}\")\n"
    "                self._use_workspace = False\n"
    "        try:\n"
    "            graph = self._load_citation_graph()\n"
    "            if not graph or not results:\n"
    "                return results, []",
    "enrich 动态图分支",
))

patch('app/knowledge.py', kn_repls)
print("全部替换完成")
