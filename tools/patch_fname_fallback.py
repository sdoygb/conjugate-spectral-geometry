# -*- coding: utf-8 -*-
"""回退 patch：enrich_with_graph 的编号→文件名映射，_articles_dir 为空时回退 ChromaDB metadata。"""
import io, sys

SRC = 'app/knowledge.py'

with io.open(SRC, encoding='utf-8') as f:
    src = f.read()

old = """            # 3. 编号 -> 文件名映射（从文章目录扫描）
            id_to_fname = {}
            try:
                for fname in os.listdir(self._articles_dir):
                    _m = re.match(r'^(\\d{1,2}\\.\\d{1,2})', fname)
                    if _m:
                        id_to_fname.setdefault(_m.group(1), fname)
            except Exception:
                pass
"""

new = """            # 3. 编号 -> 文件名映射（从文章目录扫描；目录为空时回退 ChromaDB metadata）
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
                    _cache = {}
                    try:
                        _got = self._safe_collection_call(
                            'articles_collection', 'get', include=['metadatas'])
                        for _m in (_got.get('metadatas') or []):
                            _fn = (_m or {}).get('fname', '')
                            _mm = re.match(r'^(\\d{1,2}\\.\\d{1,2})', _fn)
                            if _mm:
                                _cache.setdefault(_mm.group(1), _fn)
                    except Exception as _e:
                        logger.debug(f"[GRAPH] 编号映射回退失败: {_e}")
                    self._id_fname_cache = _cache
                id_to_fname = self._id_fname_cache
"""

count = src.count(old)
if count != 1:
    print(f"FAIL: anchor found {count} times (expect 1)")
    sys.exit(1)

src = src.replace(old, new)
with io.open(SRC, 'w', encoding='utf-8') as f:
    f.write(src)
print("OK: patch applied")
