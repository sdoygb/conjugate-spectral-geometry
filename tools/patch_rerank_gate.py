#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch: 为 rerank 增加确定性分歧检测闸门"""
p = '/Users/oygb/Downloads/GeometryAI-Mac-Build/app/knowledge.py'
src = open(p, encoding='utf-8').read()

# 1. 在 _needs_rerank 后插入 _rerank_disagreement
anchor1 = "        return any(t in query for t in _reason_tokens)\n\n    def _rerank"
new_method = """        return any(t in query for t in _reason_tokens)

    def _rerank_disagreement(self, pool: List[Dict[str, Any]]) -> bool:
        \"\"\"确定性分歧检测：RRF 混合排序与纯向量距离排序的 top5 重叠度。

        重叠度高（>=0.6）说明排序已稳定，远程 rerank 边际收益小，跳过省 ~600ms；
        重叠度低说明语义分歧大，值得精排。池子过小时保守返回 True（保持原行为）。
        \"\"\"
        if len(pool) < 6:
            return True
        _top = 5
        rrf_top = [r.get('id') for r in sorted(
            pool, key=lambda x: -x.get('_rrf_score', 0.0))[:_top]]
        dist_top = [r.get('id') for r in sorted(
            pool, key=lambda x: x.get('distance', 999.0))[:_top]]
        if not rrf_top:
            return True
        overlap = len(set(rrf_top) & set(dist_top)) / float(_top)
        stable = overlap >= 0.6
        if stable:
            logger.info(f"[RERANK] 分歧检测: top{_top} 重叠 {overlap:.0%}，排序稳定，跳过远程精排")
        return not stable

    def _rerank"""
assert src.count(anchor1) == 1, f'anchor1 count={src.count(anchor1)}'
src = src.replace(anchor1, new_method)

# 2. 调用条件加分歧检测
anchor2 = ("                    if self._needs_rerank(query):\n"
           "                        rr = self._rerank(query, docs, top_n=min(top_k * 2, len(docs)))")
new2 = ("                    if self._needs_rerank(query) and self._rerank_disagreement(pool):\n"
        "                        rr = self._rerank(query, docs, top_n=min(top_k * 2, len(docs)))")
assert src.count(anchor2) == 1, f'anchor2 count={src.count(anchor2)}'
src = src.replace(anchor2, new2)

open(p, 'w', encoding='utf-8').write(src)
print('patched OK')
