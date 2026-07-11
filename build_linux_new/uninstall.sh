#!/bin/bash
# Geometry AI Server - 卸载脚本
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${CYAN}[→]${NC} $1"; }

APP_DIR="/usr/local/geometry-ai"

echo ""
echo "  Geometry AI Server - 卸载"
echo "  ================================================"
echo ""

if [ "$EUID" -ne 0 ]; then echo "请使用 sudo 运行"; exit 1; fi

warn "停止并删除服务..."
systemctl stop geometry-ai-webui 2>/dev/null || true
systemctl stop geometry-ai 2>/dev/null || true
systemctl disable geometry-ai-webui 2>/dev/null || true
systemctl disable geometry-ai 2>/dev/null || true
rm -f /etc/systemd/system/geometry-ai.service
rm -f /etc/systemd/system/geometry-ai-webui.service
systemctl daemon-reload
info "服务已删除"

warn "删除防火墙规则..."
if command -v ufw &>/dev/null; then
    ufw delete allow 5000/tcp >/dev/null 2>&1 || true
    ufw delete allow 8080/tcp >/dev/null 2>&1 || true
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --remove-port=5000/tcp >/dev/null 2>&1 || true
    firewall-cmd --permanent --remove-port=8080/tcp >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
fi
info "防火墙规则已删除"

if id -u geometry-ai &>/dev/null; then
    userdel geometry-ai 2>/dev/null || true
    info "系统用户已删除"
fi

read -p "删除运行时数据 (chroma_db, logs)? (y/N): " ans1
if [ "$ans1" = "y" ] || [ "$ans1" = "Y" ]; then
    rm -rf "$APP_DIR/chroma_db" "$APP_DIR/logs" "$APP_DIR/venv"
    info "运行时数据已删除"
fi

read -p "删除整个安装目录? (y/N): " ans2
if [ "$ans2" = "y" ] || [ "$ans2" = "Y" ]; then
    rm -rf "$APP_DIR"
    info "安装目录已删除"
fi

echo ""
info "卸载完成"
