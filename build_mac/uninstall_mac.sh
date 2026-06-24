#!/bin/bash
# Geometry AI Server - macOS 卸载脚本
# 双击运行或在终端执行: bash uninstall_mac.sh

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     Geometry AI Server - 卸载程序               ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# 安装目录（脚本所在目录）
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${YELLOW}即将卸载 Geometry AI Server，包括：${NC}"
echo "  - 停止并删除后台服务（Geometry AI Server + Open WebUI）"
echo "  - 删除日志文件"
echo "  - 删除下载的 Python 环境"
echo ""
echo -e "${RED}注意：文章数据和配置文件会保留（不会删除）${NC}"
echo ""
read -p "确定要卸载吗？(y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# ============================================================
# Step 1: 停止并删除 launchd 服务
# ============================================================
echo ""
echo -e "${CYAN}[1/4] 停止后台服务...${NC}"

# Geometry AI Server
PLIST_SERVER="$HOME/Library/LaunchAgents/com.geometryai.server.plist"
if [ -f "$PLIST_SERVER" ]; then
    launchctl unload "$PLIST_SERVER" 2>/dev/null || true
    rm -f "$PLIST_SERVER"
    echo -e "${GREEN}[√] Geometry AI Server 服务已删除${NC}"
else
    echo "  Geometry AI Server 服务未安装"
fi

# Open WebUI
PLIST_WEBUI="$HOME/Library/LaunchAgents/com.geometryai.webui.plist"
if [ -f "$PLIST_WEBUI" ]; then
    launchctl unload "$PLIST_WEBUI" 2>/dev/null || true
    rm -f "$PLIST_WEBUI"
    echo -e "${GREEN}[√] Open WebUI 服务已删除${NC}"
else
    echo "  Open WebUI 服务未安装"
fi

# ============================================================
# Step 2: 删除日志
# ============================================================
echo ""
echo -e "${CYAN}[2/4] 清理日志文件...${NC}"

LOG_DIR="$INSTALL_DIR/logs"
if [ -d "$LOG_DIR" ]; then
    rm -f "$LOG_DIR"/*.log
    echo -e "${GREEN}[√] 日志已清理${NC}"
else
    echo "  无日志文件"
fi

# ============================================================
# Step 3: 删除下载的 Python 环境
# ============================================================
echo ""
echo -e "${CYAN}[3/4] 清理 Python 环境...${NC}"

WEBUI_PYTHON_DIR="$INSTALL_DIR/webui_python"
if [ -d "$WEBUI_PYTHON_DIR" ]; then
    rm -rf "$WEBUI_PYTHON_DIR"
    echo -e "${GREEN}[√] Open WebUI Python 环境已删除${NC}"
else
    echo "  无 Open WebUI Python 环境"
fi

# ============================================================
# Step 4: 删除安装脚本自身
# ============================================================
echo ""
echo -e "${CYAN}[4/4] 完成${NC}"

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     卸载完成！                                   ║"
echo "  ║                                                  ║"
echo "  ║     以下内容已保留（如需彻底删除请手动操作）：      ║"
echo "  ║     - 文章数据: $INSTALL_DIR/app/articles/       ║"
echo "  ║     - 向量索引: $INSTALL_DIR/app/chroma_db/      ║"
echo "  ║     - 配置文件: $INSTALL_DIR/app/.env            ║"
echo "  ║                                                  ║"
echo "  ║     彻底删除: rm -rf $INSTALL_DIR                ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
read -p "按回车退出..."
