#!/bin/bash
echo "=== 结果文件 ==="
ls -la /tmp/kb_result.json 2>/dev/null || echo "无结果文件"
if [ -s /tmp/kb_result.json ]; then
  echo "--- 内容（前2000字符） ---"
  head -c 2000 /tmp/kb_result.json
  echo ""
fi
echo ""
echo "=== curl 进程 ==="
ps aux | grep -E "curl.*vector" | grep -v grep | head -3 || echo "无 curl 进程"
echo ""
echo "=== health ==="
curl -s --max-time 5 http://127.0.0.1:5000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('articles_count:', d.get('articles_count'), '| total_docs:', d.get('total_docs'), '| vector_kb:', d.get('vector_kb_initialized'))"
