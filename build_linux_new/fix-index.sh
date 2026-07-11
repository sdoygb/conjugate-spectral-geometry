#!/bin/bash
# Geometry AI Server - 知识库索引重建
APP_DIR="/usr/local/geometry-ai"
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[!] 未找到配置文件，请先运行 setup.sh"
    exit 1
fi
if ! systemctl is-active --quiet geometry-ai; then
    echo "[!] 服务未运行"
    exit 1
fi
echo "正在重建知识库索引..."
RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)
if echo "$RESP" | grep -q '"success": true'; then
    echo "[✓] 索引重建成功"
else
    echo "[!] 索引重建请求已发送，检查日志: journalctl -u geometry-ai -n 20"
fi
