#!/bin/bash
echo "=== 1. RAG/embedding 相关日志（新进程 08:05 后） ==="
journalctl -u open-webui --no-pager --since "08:05:00" | grep -iE "sentence|embedding|rag|retriev" | head -10
echo ""
echo "=== 2. /api/config RAG 配置 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import urllib.request, json
r = json.load(urllib.request.urlopen('http://localhost:8080/api/config', timeout=10))
rag = r.get('rag', {})
print('embedding_engine:', rag.get('embedding_engine'))
print('embedding_model:', rag.get('embedding_model'))
print('top_k:', rag.get('top_k'))
"
echo ""
echo "=== 3. 数据库 config 表 RAG 键 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
rows = conn.execute(\"SELECT key, value FROM config WHERE key LIKE 'rag%' ORDER BY key\").fetchall()
for k, v in rows:
    print(k, '=', v[:100])
conn.close()
"
echo ""
echo "=== 4. 共享 venv 清理前状态 ==="
/usr/local/geometry-ai/venv/bin/pip show open-webui 2>/dev/null | head -2
/usr/local/geometry-ai/venv/bin/pip show chromadb 2>/dev/null | head -2
