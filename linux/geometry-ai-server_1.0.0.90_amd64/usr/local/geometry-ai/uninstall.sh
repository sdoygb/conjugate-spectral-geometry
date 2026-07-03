#!/bin/bash
# Geometry AI Server - 完全卸载脚本
set -e

if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash uninstall.sh"
    exit 1
fi

echo ""
echo "  ============================================================"
echo "      Geometry AI Server - 卸载"
echo "  ============================================================"
echo ""

echo "[1/4] 停止服务..."
systemctl stop geometry-ai 2>/dev/null || true
systemctl disable geometry-ai 2>/dev/null || true
echo "  [ok] 服务已停止"

echo "[2/4] 移除 systemd 服务..."
rm -f /etc/systemd/system/geometry-ai.service
systemctl daemon-reload
echo "  [ok] systemd 服务已移除"

echo "[3/4] 删除程序文件..."
APP_DIR="/usr/local/geometry-ai"
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "  [ok] 程序文件已删除 ($APP_DIR)"
fi

echo "[4/4] 清理完成"
echo ""
echo "  ============================================================"
echo "  [ok] 卸载完成！"
echo "  ============================================================"
echo ""
echo "  如需同时删除 ChromaDB 向量库和文章:"
echo "    sudo rm -rf $APP_DIR/articles $APP_DIR/chroma_db $APP_DIR/logs"
echo "  如需同时删除 Python 依赖:"
echo "    pip3 uninstall openai flask flask-cors chromadb pysqlite3-binary python-dotenv -y"
echo ""
