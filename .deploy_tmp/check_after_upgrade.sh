#!/bin/bash
echo "=== 1. /api/version ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=8))
    print('版本:', r)
except Exception as e:
    print('ERR', e)
"
echo ""
echo "=== 2. open-webui 依赖约束 ==="
/usr/local/geometry-ai/venv/bin/pip show open-webui | grep -E "Version|Requires"
echo ""
echo "=== 3. chromadb 当前版本 ==="
/usr/local/geometry-ai/venv/bin/pip show chromadb | head -2
echo ""
echo "=== 4. geometry-ai 服务状态 ==="
systemctl is-active geometry-ai
echo ""
echo "=== 5. geometry-ai 健康检查 ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:5000/health', timeout=8))
    print('vector_kb_initialized:', r.get('vector_kb_initialized'), '| total_docs:', r.get('total_docs'), '| version:', r.get('version'))
except Exception as e:
    print('ERR', e)
"
echo ""
echo "=== 6. geometry-ai 进程已加载的 chromadb ==="
ps aux | grep geometry-ai | grep -v grep | head -2
echo ""
echo "=== 7. 向量检索实测（chromadb 1.5.9 环境测试） ==="
echo 'ab640815.' | sudo -S /usr/local/geometry-ai/venv/bin/python3 -c "
import chromadb
print('chromadb 版本:', chromadb.__version__)
try:
    client = chromadb.PersistentClient(path='/usr/local/geometry-ai/chroma_db')
    cols = client.list_collections()
    print('集合数:', len(cols))
    for c in cols:
        print('  集合:', c.name, '| count:', c.count())
except Exception as e:
    print('chroma 打开失败:', type(e).__name__, e)
" 2>&1 | grep -vE "telemetry|Telemetry|anonymous"
