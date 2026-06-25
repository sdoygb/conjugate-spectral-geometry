#!/bin/bash
# Geometry AI Server - Linux 卸载脚本
set -e

echo "正在停止服务..."
sudo systemctl stop geometry-ai-webui 2>/dev/null || true
sudo systemctl stop geometry-ai 2>/dev/null || true
sudo systemctl disable geometry-ai-webui 2>/dev/null || true
sudo systemctl disable geometry-ai 2>/dev/null || true

echo "正在删除 systemd 服务文件..."
sudo rm -f /etc/systemd/system/geometry-ai.service
sudo rm -f /etc/systemd/system/geometry-ai-webui.service
sudo systemctl daemon-reload

echo "正在清理 Open WebUI 数据..."
rm -rf ~/.open-webui 2>/dev/null || true

echo "正在清理 Python 缓存..."
find "$(cd "$(dirname "$0")" && pwd)/app" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "[√] 服务已卸载"

read -p "是否删除运行时数据（向量数据库、日志等）？(y/N): " CONFIRM
if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
    rm -rf "$INSTALL_DIR/app/chroma_db"
    rm -rf "$INSTALL_DIR/app/logs"
    rm -rf "$INSTALL_DIR/app/.venv"
    rm -rf "$INSTALL_DIR/app/archive"
    echo "[√] 运行时数据已清理"
fi

read -p "是否删除整个安装目录？(y/N): " CONFIRM2
if [ "$CONFIRM2" = "y" ] || [ "$CONFIRM2" = "Y" ]; then
    INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo "正在删除: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    echo "[√] 安装目录已删除"
fi

echo ""
echo "[√] 卸载完成"
