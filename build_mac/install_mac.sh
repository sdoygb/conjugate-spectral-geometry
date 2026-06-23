#!/bin/bash
# Geometry AI Server - macOS 全自动安装脚本
# 双击运行或在终端执行: bash install_mac.sh

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     Geometry AI Server - macOS 全自动安装       ║"
echo "  ║     双击此文件，等待安装完成即可                  ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# 安装目录（脚本所在目录）
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$INSTALL_DIR/app"
LOG_DIR="$INSTALL_DIR/logs"
PYTHON_DIR="$INSTALL_DIR/python"

# ============================================================
# Step 1: 检查系统架构
# ============================================================
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    PYTHON_ARCH="arm64"
    echo -e "${CYAN}[系统] Apple Silicon (M1/M2/M3/M4) 检测到${NC}"
elif [ "$ARCH" = "x86_64" ]; then
    PYTHON_ARCH="x86_64"
    echo -e "${CYAN}[系统] Intel Mac 检测到${NC}"
else
    echo -e "${RED}[错误] 不支持的架构: $ARCH${NC}"
    read -p "按回车退出..."
    exit 1
fi

# ============================================================
# Step 2: 检查 Python
# ============================================================
echo ""
echo -e "${CYAN}[1/5] 检查 Python 环境...${NC}"

# 优先使用内嵌 Python
if [ -f "$PYTHON_DIR/bin/python3" ]; then
    PYTHON="$PYTHON_DIR/bin/python3"
    echo -e "${GREEN}[√] 使用内嵌 Python: $PYTHON${NC}"
else
    # 查找系统 Python
    if command -v python3 &>/dev/null; then
        PYTHON=$(command -v python3)
        PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo -e "${GREEN}[√] 使用系统 Python $PY_VERSION: $PYTHON${NC}"
    else
        echo -e "${YELLOW}[!] 未找到 Python，正在安装...${NC}"
        # 尝试用 Homebrew 安装
        if command -v brew &>/dev/null; then
            brew install python@3.11
            PYTHON=$(command -v python3)
        else
            # 下载内嵌 Python
            echo "正在下载 Python 3.11..."
            PYTHON_VERSION="3.11.9"
            if [ "$PYTHON_ARCH" = "arm64" ]; then
                PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.arm64.pkg"
            else
                PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
            fi
            curl -L -o /tmp/python.pkg "$PYTHON_URL"
            sudo installer -pkg /tmp/python.pkg -target /
            rm /tmp/python.pkg
            PYTHON="/usr/local/bin/python3"
        fi
        echo -e "${GREEN}[√] Python 安装完成: $PYTHON${NC}"
    fi
fi

# ============================================================
# Step 3: 安装 pip 依赖
# ============================================================
echo ""
echo -e "${CYAN}[2/5] 安装 Python 依赖（可能需要几分钟）...${NC}"

# 检查是否需要安装
NEED_INSTALL=0
if ! $PYTHON -c "import flask" 2>/dev/null; then
    NEED_INSTALL=1
fi

if [ $NEED_INSTALL -eq 1 ]; then
    # 确保 pip 可用
    if ! $PYTHON -m pip --version &>/dev/null; then
        echo "正在安装 pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON
    fi

    # 安装依赖
    $PYTHON -m pip install --quiet --disable-pip-version-check \
        -r "$APP_DIR/requirements.txt" 2>/dev/null || {
        echo -e "${YELLOW}[!] 批量安装失败，逐个安装...${NC}"
        for pkg in openai flask flask-cors chromadb; do
            echo -n "  安装 $pkg ... "
            $PYTHON -m pip install --quiet --disable-pip-version-check $pkg 2>/dev/null && echo "OK" || echo "跳过"
        done
    }
    echo -e "${GREEN}[√] Python 依赖安装完成${NC}"
else
    echo -e "${GREEN}[√] Python 依赖已安装，跳过${NC}"
fi

# ============================================================
# Step 4: 配置
# ============================================================
echo ""
echo -e "${CYAN}[3/5] 配置 API Key...${NC}"

ENV_FILE="$APP_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    if grep -q "KIMI_API_KEY=" "$ENV_FILE" && ! grep -q "KIMI_API_KEY=在此" "$ENV_FILE" && ! grep -q 'KIMI_API_KEY=$' "$ENV_FILE"; then
        echo -e "${GREEN}[√] 配置已存在，跳过（如需修改请编辑 $ENV_FILE）${NC}"
    else
        _configure
    fi
else
    _configure
fi

_configure() {
    echo ""
    echo "  请输入你的 DeepSeek API Key"
    echo "  获取地址: https://platform.deepseek.com"
    echo ""
    read -p "  API Key: " API_KEY

    if [ -z "$API_KEY" ]; then
        echo -e "${RED}[!] API Key 不能为空${NC}"
        read -p "按回车退出..."
        exit 1
    fi

    cat > "$ENV_FILE" << EOF
# Geometry AI Server 配置
KIMI_API_KEY=$API_KEY
KIMI_BASE_URL=https://api.deepseek.com/v1
KIMI_MODEL=deepseek-v4-pro
KIMI_MODEL_LITE=deepseek-v4-flash
KIMI_MODEL_VISION=deepseek-v4-flash
KIMI_EMBEDDING_MODEL=deepseek-v4-flash
EOF
    echo -e "${GREEN}[√] 配置已保存${NC}"
}

# ============================================================
# Step 5: 创建日志目录
# ============================================================
mkdir -p "$LOG_DIR"

# ============================================================
# Step 6: 注册 launchd 服务（开机自启）
# ============================================================
echo ""
echo -e "${CYAN}[4/5] 配置开机自启动...${NC}"

PLIST_NAME="com.geometryai.server"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# 停止旧服务（如果存在）
launchctl unload "$PLIST_PATH" 2>/dev/null || true

# 创建 plist
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$APP_DIR/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$APP_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/service-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/service-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GEOMETRY_AI_HOME</key>
        <string>$INSTALL_DIR</string>
    </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH" 2>/dev/null
echo -e "${GREEN}[√] 开机自启动已配置${NC}"

# ============================================================
# Step 7: 启动服务
# ============================================================
echo ""
echo -e "${CYAN}[5/5] 启动服务...${NC}"

# 等待服务启动
sleep 2

# 检查服务状态
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo -e "${GREEN}[√] 服务已启动！${NC}"
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:5000/health >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] 服务启动中，请稍候...${NC}"
    echo -e "${YELLOW}    如果 30 秒后仍无法访问，请检查日志: $LOG_DIR/${NC}"
fi

# 打开浏览器
sleep 1
open http://localhost:5000/admin

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     安装完成！                                   ║"
echo "  ║                                                  ║"
echo "  ║     管理界面: http://localhost:5000/admin        ║"
echo "  ║     聊天界面: http://localhost:3000               ║"
echo "  ║                                                  ║"
echo "  ║     停止服务: launchctl unload $PLIST_PATH  ║"
echo "  ║     启动服务: launchctl load $PLIST_PATH    ║"
echo "  ║     查看日志: $LOG_DIR/                  ║"
echo "  ║     修改配置: 编辑 $ENV_FILE              ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
