#!/bin/bash
NOW=$(date +%H:%M:%S)
echo "=== $NOW 重建进度 ==="
curl -s --max-time 5 http://127.0.0.1:5000/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
ac = d.get('articles_count', 0)
print(f'articles_count: {ac}  (旧索引 7314, 新文章 149 篇可能更多)')
print(f'total_docs: {d.get(\"total_docs\")}')
"
echo ""
if ps aux | grep "curl.*vector" | grep -v grep > /dev/null; then
  echo "curl 进程存活（重建仍在进行）"
  ps aux | grep "curl.*vector" | grep -v grep | awk '{print "  已运行:", $10}'
else
  echo "curl 进程已退出（重建请求结束）"
  ls -la /tmp/kb_result.json 2>/dev/null && echo "--- 结果 ---" && head -c 1500 /tmp/kb_result.json || echo "无结果文件"
fi
