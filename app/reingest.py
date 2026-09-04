#!/usr/bin/env python3
"""reingest.py — 重建 chroma 索引 + 导出 geo-data + 同步多位置"""
import os, sys, json, shutil, hashlib

APP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP)
sys.path.insert(0, APP)
os.chdir(APP)

from knowledge import VectorKnowledgeBase
import config

# 1. 重建 chroma 文章索引
kb = VectorKnowledgeBase(config.CHROMA_DB_DIR)
ok_init = kb.initialize()
print(f"initialize: {ok_init}")
diag = kb.build_index(config.UPLOAD_FOLDER)
print(f"build_index: files={diag.get('files_indexed')} chunks={diag.get('total_chunks')} errs={len(diag.get('errors', []))}")
if diag.get('errors'):
    print("errors:", diag['errors'][:5])

# 2. 导出 geo-data（plugin data）
export_script = os.path.join(ROOT, 'dsh-geometry-plugin', 'scripts', 'export_dsh_index.py')
rc = os.system(f'"{sys.executable}" "{export_script}"')
print(f"export_dsh_index rc={rc}")

# 3. 同步到各位置
PLUGIN_DATA = os.path.join(ROOT, 'dsh-geometry-plugin', 'data')
destinations = {
    'geo-data': os.path.join(ROOT, 'geo-data'),
}
# node_modules 里的副本（若有）
import glob
for nm in glob.glob(os.path.join(ROOT, 'node_modules', '*geometry*')):
    destinations[f'node_modules/{os.path.basename(nm)}'] = nm
# 独立 repo gk-sync
for gk in glob.glob(os.path.join(ROOT, '..', '*gk-sync*')) + glob.glob(os.path.join(ROOT, '*gk-sync*')):
    if os.path.isdir(gk):
        destinations[f'gk-sync:{os.path.basename(gk)}'] = gk

for name, dst in destinations.items():
    if not os.path.isdir(dst):
        print(f"skip {name} (missing)")
        continue
    # 拷贝 articles.jsonl / truth.jsonl / articles_toc.json / dict.json / manifest.json / articles/
    for f in ('articles.jsonl', 'truth.jsonl', 'articles_toc.json', 'dict.json', 'manifest.json'):
        src = os.path.join(PLUGIN_DATA, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, f))
    src_art = os.path.join(PLUGIN_DATA, 'articles')
    dst_art = os.path.join(dst, 'articles')
    if os.path.isdir(src_art):
        os.makedirs(dst_art, exist_ok=True)
        for f in os.listdir(src_art):
            shutil.copy2(os.path.join(src_art, f), os.path.join(dst_art, f))
    print(f"synced -> {name}")
print("DONE")
