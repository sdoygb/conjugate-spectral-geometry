#!/bin/bash
echo "=== 1. 索引等待器结果 ==="
cat /tmp/index_wait.txt 2>/dev/null || echo "(等待器文件不存在)"
echo ""
echo "=== 2. 服务状态 ==="
systemctl is-active geometry-ai
echo ""
echo "=== 3. 健康检查 ==="
curl -s http://localhost:5000/health
echo ""
echo "=== 4. 最近向量/启动日志 ==="
journalctl -u geometry-ai --no-pager --since "25 minutes ago" | grep -E "STARTUP|VECTOR|索引|ERROR" | tail -10
echo ""
echo "=== 5. 监听端口 ==="
ss -tlnp 2>/dev/null | grep 5000 || netstat -tlnp 2>/dev/null | grep 5000
