#!/bin/bash
echo "=== 1. 数据库 config 表 RAG 键（只读模式） ==="
/usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
rows = conn.execute(\"SELECT key, value FROM config WHERE key LIKE 'rag%' ORDER BY key\").fetchall()
for k, v in rows:
    print(k, '=', v[:150])
conn.close()
"
echo ""
echo "=== 2. /api/config rag 完整结构 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import urllib.request, json
r = json.load(urllib.request.urlopen('http://localhost:8080/api/config', timeout=10))
rag = r.get('rag', {})
print('rag keys:', list(rag.keys())[:20])
for k in ['embedding_engine', 'embedding_model', 'top_k']:
    if k in rag:
        print(k, '=', rag[k])
"
echo ""
echo "=== 3. 共享 venv open-webui 状态 ==="
/usr/local/geometry-ai/venv/bin/pip show open-webui 2>&1 | head -3
echo ""
echo "=== 4. 共享 venv chromadb 状态 ==="
/usr/local/geometry-ai/venv/bin/pip show chromadb 2>&1 | head -2
