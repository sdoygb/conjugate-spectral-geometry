#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch knowledge.py: enrich_with_graph 编号→文件名映射回退 ChromaDB metadata"""
import re

P = 'app/knowledge.py'
src = open(P, encoding='utf-8').read()

old = """            # 3. 编号 → 文件名映射（从文章目录扫描）
            id_to_fname = {}
            try:
                for fname in os.listdir(self._articles_dir):
                    _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
                    if _m:
                        id_to_fname.setdefault(_m.group(1), fname)
            except Exception:
                pass"""

new = """            # 3. 编号 → 文件名映射（文章目录扫描，空则回退 ChromaDB metadata）
            id_to_fname = {}
            if self._articles_dir:
                try:
                    for fname in os.listdir(self._articles_dir):
                        _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
                        if _m:
                            id_to_fname.setdefault(_m.group(1), fname)
                except Exception:
                    pass
            if not id_to_fname:
                if not hasattr(self, '_id_fname_cache') or not self._id_fname_cache:
                    try:
                        _got = self._safe_collection_call(
                            'articles_collection', 'get', include=['metadatas'])
                        _cache = {}
                        for _mm in (_got.get('metadatas') or []):
                            _fn = (_mm or {}).get('fname', '')
                            _mt = re.match(r'^(\\d{1,2}\\.\\d{1,2})', _fn)
                            if _mt:
                                _cache.setdefault(_mt.group(1), _fn)
                        self._id_fname_cache = _cache
                        print(f'[GRAPH] 编号映射回退: {len(_cache)} 篇文章')
                    except Exception as _e:
                        print(f'[GRAPH] 编号映射回退失败: {_e}')
                        self._id_fname_cache = {}
                id_to_fname = self._id_fname_cache"""

if old not in src:
    # 可能是 \d 转义差异，先打印上下文
    idx = src.find('编号 → 文件名映射')
    if idx == -1:
        print('ERROR: 找不到 "编号 → 文件名映射"')
        raise SystemExit(1)
    print('--- 原文上下文 ---')
    print(src[idx-100:idx+600])
    raise SystemExit(1)

src = src.replace(old, new, 1)
open(P, 'w', encoding='utf-8').write(src)
print('patched OK')
