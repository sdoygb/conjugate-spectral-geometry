#!/bin/bash
echo "=== 1. 检查 geometry-ai 是否引用 open_webui 包 ==="
grep -rn "import open_webui\|from open_webui" /usr/local/geometry-ai/*.py /usr/local/geometry-ai/*/*.py 2>/dev/null | head -5
if [ $? -ne 0 ]; then echo "无引用（安全卸载）"; fi
echo ""
echo "=== 2. 卸载共享 venv 中的 open-webui ==="
/usr/local/geometry-ai/venv/bin/pip uninstall -y open-webui 2>&1 | tail -2
echo ""
echo "=== 3. 共享 venv chromadb 版本确认 ==="
/usr/local/geometry-ai/venv/bin/pip show chromadb 2>/dev/null | grep -E "Name|Version"
echo ""
echo "=== 4. 新 venv 版本确认 ==="
/usr/local/open-webui-venv/bin/pip show open-webui 2>/dev/null | grep -E "Name|Version"
/usr/local/open-webui-venv/bin/pip show chromadb 2>/dev/null | grep -E "Name|Version"
echo ""
echo "=== 5. geometry-ai 健康 ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:5000/health', timeout=8))
    print('vector_kb:', r.get('vector_kb_initialized'), '| docs:', r.get('total_docs'), '| teaching:', r.get('teaching_system'))
except Exception as e:
    print('ERR', type(e).__name__, e)
"
echo ""
echo "=== 6. open-webui RAG 配置检查 ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/config', timeout=8))
    rag = r.get('rag', {})
    print('embedding_engine:', rag.get('embedding_engine'))
    print('embedding_model:', rag.get('embedding_model'))
    print('openai_base:', str(rag.get('openai', {}).get('api_base_url', ''))[:70])
    print('openai_key_set:', bool(rag.get('openai', {}).get('api_key', '')))
except Exception as e:
    print('ERR', type(e).__name__, e)
"
echo ""
echo "=== 7. open-webui 最新日志（RAG/embedding 相关） ==="
journalctl -u open-webui --no-pager --since "5 minutes ago" | grep -iE "sentence|rag|embedding|error" | head -6 || echo "无相关错误"
