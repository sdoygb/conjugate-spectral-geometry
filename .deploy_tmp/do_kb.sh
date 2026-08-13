#!/bin/bash
echo "=== 重建前状态 ==="
curl -s --max-time 5 http://127.0.0.1:5000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('articles_count:', d.get('articles_count'), '| total_docs:', d.get('total_docs'), '| vector_kb:', d.get('vector_kb_initialized'))"
echo ""
echo "=== 触发重建（后台） ==="
rm -f /tmp/kb_result.json
nohup curl -s -X POST --max-time 900 http://127.0.0.1:5000/v1/vector/rebuild -o /tmp/kb_result.json > /dev/null 2>&1 &
echo "后台启动 pid=$!"
sleep 8
echo "8 秒后结果文件大小: $(wc -c < /tmp/kb_result.json 2>/dev/null || echo 0) 字节"
