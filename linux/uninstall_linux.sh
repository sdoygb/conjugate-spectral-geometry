#!/bin/bash
# Geometry AI Server - Linux 卸载脚本
set -e

echo "正在停止服务..."
sudo systemctl stop geometry-ai-webui 2>/dev/null || true
sudo systemctl stop geometry-ai 2>/dev/null || true
sudo systemctl disable geometry-ai-webui 2>/dev/null || true
sudo systemctl disable geometry-ai 2>/dev/null || true
sudo rm -f /etc/systemd/system/geometry-ai.service
sudo rm -f /etc/systemd/system/geometry-ai-webui.service
sudo systemctl daemon-reload
echo "[√] 服务已卸载"

read -p "是否删除安装目录？(y/N): " CONFIRM
if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
    rm -rf "$INSTALL_DIR/app/chroma_db" "$INSTALL_DIR/app/logs" "$INSTALL_DIR/app/.venv"
    echo "[√] 运行时数据已清理"
    echo "    如需完全删除，请手动删除: $INSTALL_DIR"
fi

echo "[√] 卸载完成"
