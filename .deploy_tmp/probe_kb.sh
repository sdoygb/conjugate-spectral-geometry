#!/bin/bash
echo "=== 1. geometry-ai 进程与端口 ==="
ps aux | grep -iE "geometry|uvicorn|fastapi|chroma" | grep -v grep | head -8
ss -tlnp | grep -E ":5000|:8081|:8000" | head -5
echo ""
echo "=== 2. /usr/local/geometry-ai 结构 ==="
ls -la /usr/local/geometry-ai/ 2>/dev/null
echo ""
echo "=== 3. 文章源与向量库目录 ==="
find /usr/local/geometry-ai -maxdepth 3 -type d 2>/dev/null | head -30
echo ""
echo "=== 4. systemd 服务 ==="
systemctl list-units --type=service --all 2>/dev/null | grep -iE "geometry|kb|vector|rag" | head -5
systemctl cat geometry-ai 2>/dev/null | grep -E "ExecStart|WorkingDirectory|Environment" | head -10
echo ""
echo "=== 5. health 探测 ==="
curl -s --max-time 5 http://127.0.0.1:5000/health 2>/dev/null || echo "5000 /health 无响应"
echo "---"
curl -s --max-time 5 http://127.0.0.1:5000/api/health 2>/dev/null || echo "5000 /api/health 无响应"
echo ""
echo "=== 6. 向量库数据目录 ==="
ls -la /usr/local/geometry-ai/chroma_db 2>/dev/null | head -10
ls -la /usr/local/geometry-ai/data 2>/dev/null | head -10
du -sh /usr/local/geometry-ai/* 2>/dev/null | head -15
