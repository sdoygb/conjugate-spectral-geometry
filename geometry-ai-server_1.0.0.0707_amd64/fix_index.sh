#!/bin/bash
# Geometry AI Server - 索引重建脚本
# 不用 set -e，apt 等命令可能返回非零但实际成功

if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash fix_index.sh"
    exit 1
fi

APP_DIR="/usr/local/geometry-ai"

echo "[1] 检查 API Key..."
if grep -q 'GAI_API_KEY=在此' "$APP_DIR/.env" 2>/dev/null; then
    echo "[!] 错误: API Key 未配置！"
    echo "    请先执行: sudo nano $APP_DIR/.env"
    exit 1
fi
echo "  [ok] API Key 已配置"

echo "[2] 检查文章文件..."
COUNT=$(ls "$APP_DIR/articles"/*.md 2>/dev/null | wc -l)
echo "  文章文件数: $COUNT"
if [ "$COUNT" -eq 0 ]; then
    echo "[!] 错误: 文章目录为空！"
    exit 1
fi

echo "[3] 检查服务状态..."
if ! systemctl is-active --quiet geometry-ai; then
    echo "  服务未运行，重新启动..."
    systemctl start geometry-ai
    sleep 5
fi

echo "[4] 触发重建索引..."
RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)
echo "  响应: $RESP"

if echo "$RESP" | grep -q '"success": true'; then
    echo "  [ok] 索引重建成功！"
else
    echo "  [!] 索引重建失败，查看日志:"
    echo "  sudo journalctl -u geometry-ai -n 50"
fi
