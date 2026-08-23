#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch: rerank 降频 + 缓存（确定性化的一部分）"""
import io, sys

PATH = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/knowledge.py'
src = io.open(PATH, encoding='utf-8').read()
orig = src
n = 0

def rep(old, new, must=True):
    global src, n
    c = src.count(old)
    if c == 0:
        if must:
            print('FAIL anchor not found:', old[:80].replace('\n', '\\n'))
            sys.exit(1)
        return
    src = src.replace(old, new, 1)
    n += 1
    print(f'  ok ({c} found): {old[:60].replace(chr(10), " ")}')

# 1. _rerank 方法开头插入缓存读取
rep(
"""    def _rerank(self, query: str, documents: List[str], top_n: int = 20):
        \"\"\"bge-reranker-v2-m3 重排（SiliconFlow rerank API）。

        对候选池按相关性重新排序，弥补向量检索在术语鸿沟上的不足。
        失败时返回 None，调用方保持原排序。
        \"\"\"
        if not documents:
            return None
        try:""",
"""    _RERANK_TTL = 600.0  # rerank 结果缓存 TTL（秒）

    def _needs_rerank(self, query: str) -> bool:
        \"\"\"推理类查询需要语义精排；纯事实查询用 RRF+距离确定性排序已足够。

        降频依据：rerank 是远程 API（~500ms），事实查询（"什么是X"/"X是多少"）
        的检索目标明确，向量距离+BM25+RRF 排序已可靠；推理类查询（推导/证明/
        对比/关系）语义跨度大，精排的边际收益才值得支付 API 延迟。
        \"\"\"
        if not query:
            return False
        _reason_tokens = ('推导', '证明', '验证', '检验', '为什么', '如何', '怎样',
                          '关系', '对比', '区别', '联系', '链条', '推广', '适用',
                          '能否', '是否', '解释', '原因', '机制', '分析', '讨论',
                          '完整', '闭合', '成立')
        return any(t in query for t in _reason_tokens)

    def _rerank(self, query: str, documents: List[str], top_n: int = 20):
        \"\"\"bge-reranker-v2-m3 重排（SiliconFlow rerank API）。

        对候选池按相关性重新排序，弥补向量检索在术语鸿沟上的不足。
        失败时返回 None，调用方保持原排序。
        带结果缓存：同查询同文档池 TTL 内不重复调用 API。
        \"\"\"
        if not documents:
            return None
        # 结果缓存：query + 文档池指纹（长度 + 首文档前缀）
        cache_key = query + '|' + str(len(documents)) + '|' + documents[0][:60]
        _now = time.time()
        if hasattr(self, '_rerank_cache'):
            _entry = self._rerank_cache.get(cache_key)
            if _entry and _now - _entry[0] < self._RERANK_TTL:
                logger.debug(f"[RERANK] 缓存命中: {len(documents)} docs")
                return _entry[1]
        try:""")

# 2. 成功返回处写入缓存
rep(
"""            if resp.status_code == 200:
                return resp.json()
            logger.debug(f"[RERANK] HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.debug(f"[RERANK] 调用失败: {e}")
        return None""",
"""            if resp.status_code == 200:
                _result = resp.json()
                if not hasattr(self, '_rerank_cache'):
                    self._rerank_cache = {}
                self._rerank_cache[cache_key] = (_now, _result)
                if len(self._rerank_cache) > 256:
                    _oldest = min(self._rerank_cache, key=lambda k: self._rerank_cache[k][0])
                    del self._rerank_cache[_oldest]
                return _result
            logger.debug(f"[RERANK] HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.debug(f"[RERANK] 调用失败: {e}")
        return None""")

# 3. search 里 rerank 调用处加推理类判断
rep(
"""                if len(pool) >= 3:
                    docs = [r.get('text', '')[:600] for r in pool]
                    rr = self._rerank(query, docs, top_n=min(top_k * 2, len(docs)))""",
"""                if len(pool) >= 3:
                    docs = [r.get('text', '')[:600] for r in pool]
                    rr = None
                    if self._needs_rerank(query):
                        rr = self._rerank(query, docs, top_n=min(top_k * 2, len(docs)))""")

io.open(PATH, 'w', encoding='utf-8').write(src)
print(f'DONE: {n} replacements, {len(orig)} -> {len(src)} chars')
