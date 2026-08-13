#!/bin/bash
echo "========== chromadb 降级 + 双服务重启 $(date +%F_%T) =========="
echo "=== 1. 降级 chromadb 到 0.6.3 ==="
/usr/local/geometry-ai/venv/bin/pip install "chromadb==0.6.3" 2>&1 | tail -4
echo ""
echo "=== 2. 版本确认 ==="
/usr/local/geometry-ai/venv/bin/pip show chromadb | head -2
echo ""
echo "=== 3. 重启 open-webui ==="
systemctl restart open-webui
sleep 12
echo "open-webui: $(systemctl is-active open-webui)"
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=8))
    print('版本响应:', r)
except Exception as e:
    print('ERR', e)
"
echo ""
echo "=== 4. 重启 geometry-ai ==="
systemctl restart geometry-ai
sleep 15
echo "geometry-ai: $(systemctl is-active geometry-ai)"
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:5000/health', timeout=12))
    print('vector_kb:', r.get('vector_kb_initialized'), '| docs:', r.get('total_docs'), '| teaching:', r.get('teaching_system'), '| version:', r.get('version'))
except Exception as e:
    print('ERR', e)
"
echo ""
echo "=== 5. geometry-ai 启动日志（chroma/BM25/ERROR） ==="
journalctl -u geometry-ai --no-pager --since "3 minutes ago" | grep -E "Chroma|BM25|VECTOR|STARTUP|ERROR|Traceback" | head -12
echo ""
echo "=== 6. open-webui 启动日志（ERROR） ==="
journalctl -u open-webui --no-pager --since "3 minutes ago" | grep -iE "error|traceback|exception" | head -8
echo "========== 结束 $(date +%F_%T) =========="
