#!/bin/bash
echo "=== 1. 服务文件关键环境变量 ==="
grep -E "WEBUI_SECRET_KEY|RAG_EMBEDDING|RAG_OPENAI|OPENWEBUI_DATA_DIR|OFFLINE_MODE" /etc/systemd/system/open-webui.service | sed 's/sk-[a-zA-Z0-9]*/sk-***/' 
echo ""
echo "=== 2. 数据库 rag 配置 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
rows = conn.execute(\"SELECT key, value FROM config WHERE key LIKE 'rag%' ORDER BY key\").fetchall()
for k, v in rows:
    print(k, '=', v[:200])
conn.close()
" 2>&1 | head -15
echo ""
echo "=== 3. SiliconFlow embedding API 连通性 ==="
KEY=$(grep -oP 'RAG_OPENAI_API_KEY=\K[^"]+' /etc/systemd/system/open-webui.service | head -1)
if [ -z "$KEY" ]; then echo "未找到 API KEY"; else
/usr/local/open-webui-venv/bin/python3 -c "
import urllib.request, json
key = '$KEY'
req = urllib.request.Request('https://api.siliconflow.cn/v1/embeddings',
    data=json.dumps({'model': 'BAAI/bge-m3', 'input': ['共扼谱几何测试']}).encode(),
    headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=15))
    print('embedding OK, dim:', len(r['data'][0]['embedding']), '| model:', r.get('model'))
except Exception as e:
    print('ERR:', e)
"
fi
echo ""
echo "=== 4. open-webui 进程确认 ==="
ps aux | grep "open-webui serve" | grep -v grep | awk '{print $2, $11}'
echo ""
echo "=== 5. geometry-ai 健康 ==="
python3 -c "
import urllib.request, json
r = json.load(urllib.request.urlopen('http://localhost:5000/health', timeout=10))
print('vector_kb:', r.get('vector_kb_initialized'), '| docs:', r.get('total_docs'))
"
