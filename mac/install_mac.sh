#!/bin/bash
# Geometry AI Server - macOS 全自动安装脚本
# 双击运行或在终端执行: bash install_mac.sh
#
# 功能：自动安装 Geometry AI Server + Open WebUI + 开机自启
# 要求：macOS 12+，需要网络连接

set -e

# ============================================================
# 函数定义
# ============================================================
_do_configure() {
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

_wait_for_url() {
    # 等待 URL 可访问，最多 $1 秒
    local url="$1"
    local max_wait="$2"
    local waited=0
    while [ "$waited" -lt "$max_wait" ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done
    return 1
}

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

mkdir -p "$LOG_DIR"

# ============================================================
# Step 1: 准备 Python 环境
# ============================================================
echo -e "${CYAN}[1/6] 准备 Python 环境...${NC}"

# 清除可能干扰的 Python 环境变量
unset PYTHONHOME
unset PYTHONPATH

# 查找可用的 Python 3.11+
PYTHON=""
for py in "/usr/local/bin/python3.11" "/opt/homebrew/bin/python3.11" "/usr/local/bin/python3.12" "/opt/homebrew/bin/python3.12"; do
    if [ -x "$py" ]; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    # 尝试使用安装包自带的 Python 3.11
    PKG_PATH="$INSTALL_DIR/python3.11.pkg"
    if [ -f "$PKG_PATH" ]; then
        echo "  正在安装 Python 3.11（需要输入电脑密码）..."
        sudo installer -pkg "$PKG_PATH" -target / 2>/dev/null
        # 刷新链接
        for py in "/usr/local/bin/python3.11" "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"; do
            if [ -x "$py" ]; then
                PYTHON="$py"
                break
            fi
        done
    fi
fi

if [ -z "$PYTHON" ]; then
    # 尝试 brew 安装
    if command -v brew &>/dev/null; then
        echo "  正在通过 Homebrew 安装 Python 3.11..."
        brew install python@3.11 2>/dev/null || true
        brew link python@3.11 --overwrite 2>/dev/null || true
        for py in "/usr/local/bin/python3.11" "/opt/homebrew/bin/python3.11"; do
            if [ -x "$py" ]; then
                PYTHON="$py"
                break
            fi
        done
    fi
fi

if [ -z "$PYTHON" ]; then
    echo -e "${RED}[!] 未找到合适的 Python（需要 3.11+）${NC}"
    echo "  请先安装 Python 3.11: https://www.python.org/downloads/"
    read -p "按回车退出..."
    exit 1
fi

PY_VERSION="$("$PYTHON" --version 2>&1 | awk '{print $2}')"
echo -e "${GREEN}[√] Python $PY_VERSION: $PYTHON${NC}"

# ============================================================
# Step 2: 安装 Geometry AI Server 依赖
# ============================================================
echo ""
echo -e "${CYAN}[2/6] 安装 Geometry AI Server 依赖...${NC}"

if "$PYTHON" -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}[√] 依赖已安装，跳过${NC}"
else
    if ! "$PYTHON" -m pip --version &>/dev/null; then
        echo "  正在安装 pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | "$PYTHON" 2>/dev/null
    fi
    echo "  正在安装依赖（可能需要几分钟）..."
    "$PYTHON" -m pip install --quiet --disable-pip-version-check \
        -r "$APP_DIR/requirements.txt" 2>/dev/null || {
        echo -e "${YELLOW}[!] 批量安装失败，逐个安装...${NC}"
        for pkg in openai flask flask-cors chromadb; do
            "$PYTHON" -m pip install --quiet --disable-pip-version-check "$pkg" 2>/dev/null
        done
    }
    echo -e "${GREEN}[√] 依赖安装完成${NC}"
fi

# ============================================================
# Step 3: 配置 API Key
# ============================================================
echo ""
echo -e "${CYAN}[3/6] 配置 API Key...${NC}"

ENV_FILE="$APP_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    if grep -q "KIMI_API_KEY=" "$ENV_FILE" && ! grep -q 'KIMI_API_KEY=$' "$ENV_FILE" && ! grep -q "KIMI_API_KEY=在此" "$ENV_FILE"; then
        echo -e "${GREEN}[√] 配置已存在，跳过${NC}"
    else
        _do_configure
    fi
else
    _do_configure
fi

# ============================================================
# Step 4: 启动 Geometry AI Server
# ============================================================
echo ""
echo -e "${CYAN}[4/6] 启动 Geometry AI Server...${NC}"

PLIST_NAME="com.geometryai.server"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# 停止旧服务
launchctl unload "$PLIST_PATH" 2>/dev/null || true
# 也杀掉可能残留的进程
lsof -ti :5000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

# 创建 plist（清除 PYTHONHOME 避免干扰）
cat > "$PLIST_PATH" << PLISTEOF
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
    <string>$LOG_DIR/server-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/server-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GEOMETRY_AI_HOME</key>
        <string>$INSTALL_DIR</string>
        <key>PYTHONHOME</key>
        <string></string>
        <key>PYTHONPATH</key>
        <string></string>
    </dict>
</dict>
</plist>
PLISTEOF

launchctl load "$PLIST_PATH" 2>/dev/null

# 等待启动
if _wait_for_url "http://localhost:5000/health" 30; then
    echo -e "${GREEN}[√] Geometry AI Server 已启动（端口 5000）${NC}"
else
    echo -e "${YELLOW}[!] Geometry AI Server 启动较慢，请稍候...${NC}"
fi

# ============================================================
# Step 5: 安装并启动 Open WebUI
# ============================================================
echo ""
echo -e "${CYAN}[5/6] 安装 Open WebUI（聊天界面）...${NC}"

# 设置 HuggingFace 镜像（国内网络加速）
export HF_ENDPOINT="https://hf-mirror.com"
export SENTENCE_TRANSFORMERS_HOME="$INSTALL_DIR/models_cache"

if "$PYTHON" -c "import open_webui" 2>/dev/null; then
    echo -e "${GREEN}[√] Open WebUI 已安装${NC}"
else
    echo "  正在安装 Open WebUI（需要几分钟，首次会下载模型）..."
    echo "  使用国内镜像加速..."
    "$PYTHON" -m pip install --quiet --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        open-webui 2>/dev/null
    if "$PYTHON" -c "import open_webui" 2>/dev/null; then
        echo -e "${GREEN}[√] Open WebUI 安装完成${NC}"
    else
        echo -e "${YELLOW}[!] Open WebUI 安装失败，聊天功能暂不可用${NC}"
        echo "  可稍后手动运行: $PYTHON -m pip install open-webui"
    fi
fi

# ============================================================
# Step 5: 安装并启动 Open WebUI
# ============================================================
echo ""
echo -e "${CYAN}[5/6] 安装 Open WebUI（聊天界面）...${NC}"

# 设置 HuggingFace 镜像（国内网络加速）
export HF_ENDPOINT="https://hf-mirror.com"
export SENTENCE_TRANSFORMERS_HOME="$INSTALL_DIR/models_cache"

if "$PYTHON" -c "import open_webui" 2>/dev/null; then
    echo -e "${GREEN}[√] Open WebUI 已安装${NC}"
else
    echo "  正在安装 Open WebUI（需要几分钟，首次会下载模型）..."
    echo "  使用国内镜像加速..."
    "$PYTHON" -m pip install --quiet --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        open-webui 2>/dev/null
    if "$PYTHON" -c "import open_webui" 2>/dev/null; then
        echo -e "${GREEN}[√] Open WebUI 安装完成${NC}"
    else
        echo -e "${YELLOW}[!] Open WebUI 安装失败，聊天功能暂不可用${NC}"
        echo "  可稍后手动运行: $PYTHON -m pip install open-webui"
        # 跳过启动
        WEBUI_SKIP=1
    fi
fi

if [ "$WEBUI_SKIP" != "1" ]; then
    # 查找 open-webui 命令路径
    WEBUI_BIN=""
    for bin_path in \
        "/usr/local/bin/open-webui" \
        "/opt/homebrew/bin/open-webui" \
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/open-webui" \
        "$("$PYTHON" -c 'import sys; print(sys.exec_prefix)')/bin/open-webui"; do
        if [ -x "$bin_path" ]; then
            WEBUI_BIN="$bin_path"
            break
        fi
    done

    if [ -z "$WEBUI_BIN" ]; then
        WEBUI_BIN="$PYTHON"
        WEBUI_ARGS_ARRAY=("-m" "open_webui.main")
    else
        WEBUI_ARGS_ARRAY=("serve")
    fi

    echo ""
    echo -e "${CYAN}  正在启动 Open WebUI（首次启动需下载模型，请耐心等待）...${NC}"

    WEBUI_PLIST="$HOME/Library/LaunchAgents/com.geometryai.webui.plist"
    launchctl unload "$WEBUI_PLIST" 2>/dev/null || true
    lsof -ti :8080 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1

    # 生成 plist
    {
        cat << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.geometryai.webui</string>
    <key>ProgramArguments</key>
    <array>
        <string>$WEBUI_BIN</string>
PLISTEOF
        for arg in "${WEBUI_ARGS_ARRAY[@]}"; do
            echo "        <string>$arg</string>"
        done
        cat << PLISTEOF2
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/webui-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/webui-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENAI_API_BASE_URLS</key>
        <string>http://localhost:5000/v1</string>
        <key>OPENAI_API_KEYS</key>
        <string>not-needed</string>
        <key>HF_ENDPOINT</key>
        <string>https://hf-mirror.com</string>
        <key>SENTENCE_TRANSFORMERS_HOME</key>
        <string>$INSTALL_DIR/models_cache</string>
        <key>PYTHONHOME</key>
        <string></string>
        <key>PYTHONPATH</key>
        <string></string>
    </dict>
</dict>
</plist>
PLISTEOF2
    } > "$WEBUI_PLIST"

    launchctl load "$WEBUI_PLIST" 2>/dev/null

    echo -e "${YELLOW}  首次启动需要下载嵌入模型（约 90MB），请耐心等待...${NC}"
    echo -e "${YELLOW}  如果网络较慢，可能需要 5-10 分钟${NC}"

    if _wait_for_url "http://localhost:8080" 300; then
        echo -e "${GREEN}[√] Open WebUI 已启动（端口 8080）${NC}"
    else
        echo -e "${YELLOW}[!] Open WebUI 启动超时${NC}"
        echo "  请稍后访问 http://localhost:8080"
        echo "  查看日志: $LOG_DIR/webui-stderr.log"
    fi
fi

# ============================================================
# Step 6: 打开浏览器
# ============================================================
echo ""
echo -e "${CYAN}[6/6] 打开浏览器...${NC}"

sleep 1

# 打开管理界面
open http://localhost:5000/admin 2>/dev/null || true

# 打开聊天界面
if curl -s http://localhost:8080 >/dev/null 2>&1; then
    open http://localhost:8080 2>/dev/null || true
fi

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║     安装完成！                                   ║"
echo "  ║                                                  ║"
echo "  ║     管理界面: http://localhost:5000/admin        ║"
echo "  ║     聊天界面: http://localhost:8080              ║"
echo "  ║                                                  ║"
echo "  ║     聊天界面首次使用：                            ║"
echo "  ║     1. 打开 http://localhost:8080                ║"
echo "  ║     2. 注册管理员账号                            ║"
echo "  ║     3. 登录后点左下角头像 → Settings             ║"
echo "  ║     4. 左侧选 Connections                        ║"
echo "  ║     5. 确认 URL 为 http://localhost:5000/v1     ║"
echo "  ║     6. 回到聊天页，选择 deepseek-v4-pro 模型     ║"
echo "  ║     7. 开始聊天！                                ║"
echo "  ║                                                  ║"
echo "  ║     两个服务已设置为开机自动启动                  ║"
echo "  ║                                                  ║"
echo "  ║     卸载: 双击 uninstall_mac.sh                  ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

exit 0
