#!/bin/bash
echo "=== 1. REBUILD 等待器结果 ==="
cat /tmp/rebuild_wait.txt 2>/dev/null || echo "等待器文件不存在"
echo ""
echo "=== 2. rebuild 返回 ==="
cat /tmp/rebuild_result.txt 2>/dev/null | head -40
echo ""
echo "=== 3. 服务状态 ==="
systemctl is-active geometry-ai
echo ""
echo "=== 4. 健康检查 ==="
curl -s http://localhost:5000/health
echo ""
echo "=== 5. 最近日志 ==="
journalctl -u geometry-ai --no-pager -n 200 | grep -E "VECTOR|BM25|STARTUP|ERROR|检索" | tail -20
echo ""
echo "=== 6. 对话测试 ==="
curl -s -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"请用共扼谱几何介绍什么是谱刚性，并说明S_e锁定的含义"}]}' \
  --max-time 90 | head -c 3000
echo ""
echo "=== DONE ==="
