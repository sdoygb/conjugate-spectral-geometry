#!/bin/bash
# Geometry AI Server - Ubuntu 卸载脚本 v1.0.0.0707
# 不用 set -e，apt 等命令可能返回非零但实际成功

APP_DIR="/usr/local/geometry-ai"

echo ""
echo "  ========================================================="
echo "      Geometry AI Server v1.0.0.0707 - 卸载"
echo "  ========================================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash uninstall.sh"
    exit 1
fi

echo "[1/4] 停止服务..."
systemctl stop geometry-ai 2>/dev/null || true
systemctl disable geometry-ai 2>/dev/null || true
echo "  [ok] 服务已停止"

echo "[2/4] 删除 systemd 服务文件..."
rm -f /etc/systemd/system/geometry-ai.service
systemctl daemon-reload
echo "  [ok] systemd 已清理"

echo "[3/4] 卸载 pip 依赖..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    echo "  以下依赖将被卸载:"
    cat "$APP_DIR/requirements.txt"
    read -p "  确认卸载这些 pip 包？(y/N): " CONFIRM_PIP
    if [ "$CONFIRM_PIP" = "y" ] || [ "$CONFIRM_PIP" = "Y" ]; then
        pip3 uninstall -y -r "$APP_DIR/requirements.txt" 2>/dev/null || true
        echo "  [ok] pip 依赖已卸载"
    else
        echo "  跳过 pip 依赖卸载"
    fi
else
    echo "  跳过（未找到 requirements.txt）"
fi

read -p "是否删除向量数据库和日志？(y/N): " CONFIRM_DATA
if [ "$CONFIRM_DATA" = "y" ] || [ "$CONFIRM_DATA" = "Y" ]; then
    rm -rf "$APP_DIR/chroma_db" 2>/dev/null || true
    rm -rf "$APP_DIR/logs" 2>/dev/null || true
    rm -rf "$APP_DIR/models_cache" 2>/dev/null || true
    echo "  [ok] 运行时数据已删除"
else
    echo "  保留运行时数据"
fi

read -p "是否删除整个安装目录 $APP_DIR？(y/N): " CONFIRM_DIR
if [ "$CONFIRM_DIR" = "y" ] || [ "$CONFIRM_DIR" = "Y" ]; then
    rm -rf "$APP_DIR"
    echo "  [ok] 安装目录已删除"
else
    echo "  保留安装目录"
fi

echo ""
echo "  ========================================================="
echo "  [ok] 卸载完成！"
echo "  ========================================================="
echo ""
