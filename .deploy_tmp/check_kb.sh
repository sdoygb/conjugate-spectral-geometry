#!/bin/bash
echo "等待重建完成（最多 100 秒轮询）..."
for i in $(seq 1 10); do
  sleep 10
  if [ -s /tmp/kb_result.json ]; then
    echo "重建完成（约 $((i*10)) 秒后检测到结果）"
    break
  fi
done
echo ""
echo "=== 重建结果 ==="
if [ -s /tmp/kb_result.json ]; then
  python3 -m json.tool /tmp/kb_result.json 2>/dev/null | head -60 || cat /tmp/kb_result.json | head -30
else
  echo "结果文件仍为空——重建可能还在进行"
  echo "检查 curl 进程是否存活:"
  ps aux | grep -E "curl.*vector" | grep -v grep | head -3 || echo "curl 进程已退出（可能失败）"
fi
echo ""
echo "=== 当前 health ==="
curl -s --max-time 5 http://127.0.0.1:5000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('articles_count:', d.get('articles_count'), '| total_docs:', d.get('total_docs'), '| vector_kb:', d.get('vector_kb_initialized'))"
