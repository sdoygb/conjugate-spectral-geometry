#!/bin/bash
# Geometry AI Server - Linux 全自动安装
set -e

echo ""
echo "  ========================================================"
echo "      Geometry AI Server - Linux 全自动安装"
echo "      运行: sudo bash install_linux.sh"
echo "  ========================================================"
echo ""

# 检测 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行此脚本"
    exit 1
fi

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$INSTALL_DIR/app"
SERVICE_USER="${SUDO_USER:-root}"

# Step 1: 检查/安装 Python 3.11+
echo "[1/6] 检查 Python 环境..."

PYTHON=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  未找到 Python 3.11+，正在安装..."
    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y software-properties-common
        add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
        apt-get install -y python3.11 python3.11-venv python3-pip
        PYTHON=python3.11
    elif command -v yum &>/dev/null; then
        yum install -y python3.11 python3.11-pip
        PYTHON=python3.11
    elif command -v dnf &>/dev/null; then
        dnf install -y python3.11 python3.11-pip
        PYTHON=python3.11
    else
        echo "[!] 不支持的系统，请手动安装 Python 3.11+"
        exit 1
    fi
fi

echo "  [√] 使用 $PYTHON ($($PYTHON --version 2>&1))"

# Step 2: 安装依赖
echo ""
echo "[2/6] 安装 Python 依赖..."
"$PYTHON" -m pip install --quiet --disable-pip-version-check \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r "$APP_DIR/requirements.txt"
echo "  [√] 依赖安装完成"

# Step 3: 配置 API Key
echo ""
echo "[3/6] 配置 API Key..."

ENV_FILE="$APP_DIR/.env"
NEED_CONFIG=0

if [ -f "$ENV_FILE" ]; then
    if grep -q "GAI_API_KEY=在此" "$ENV_FILE" 2>/dev/null || ! grep -q "GAI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
        NEED_CONFIG=1
    fi
else
    NEED_CONFIG=1
fi

if [ "$NEED_CONFIG" -eq 1 ]; then
    echo ""
    echo "  请输入你的 DeepSeek API Key（免费注册: https://platform.deepseek.com/）"
    read -p "  API Key: " API_KEY

    if [ -z "$API_KEY" ]; then
        echo "[!] API Key 不能为空"
        exit 1
    fi

    echo ""
    echo "  请输入你的 SiliconFlow API Key（向量数据库，免费注册: https://cloud.siliconflow.cn/）"
    echo "  （直接回车可跳过，将使用本地 embedding 模型）"
    read -p "  SiliconFlow API Key: " SILICONFLOW_KEY
    SILICONFLOW_KEY="${SILICONFLOW_KEY:-not-needed}"

    cat > "$ENV_FILE" << ENVEOF
# Geometry AI Server 配置
GAI_API_KEY=$API_KEY
GAI_BASE_URL=https://api.deepseek.com/v1
GAI_MODEL=deepseek-v4-pro
GAI_MODEL_LITE=deepseek-v4-flash
GAI_MODEL_VISION=deepseek-v4-flash
GAI_EMBEDDING_MODEL=deepseek-v4-flash
GAI_EMBEDDING_MODE=siliconflow
SILICONFLOW_API_KEY=$SILICONFLOW_KEY
ENVEOF
    echo "  [√] 配置已保存"
else
    echo "  [√] 配置已存在，跳过"
fi

# Step 4: 停止旧服务
echo ""
echo "[4/6] 停止旧服务..."
systemctl stop geometry-ai 2>/dev/null || true
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Step 5: 注册 systemd 服务
echo ""
echo "[5/6] 注册 systemd 服务..."

SERVICE_FILE="/etc/systemd/system/geometry-ai.service"
cat > "$SERVICE_FILE" << SVCEOF
[Unit]
Description=Geometry AI Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON $APP_DIR/server.py
Restart=always
RestartSec=5
Environment=PYTHONHOME=
Environment=PYTHONPATH=
Environment=GEOMETRY_AI_HOME=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable geometry-ai
systemctl start geometry-ai
echo "  [√] 已注册为 systemd 服务（开机自启）"

# 等待启动
echo "  等待服务启动..."
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "  [√] Geometry AI Server 已启动（端口 5000）"
        break
    fi
    sleep 2
done

# Step 6: 安装 Open WebUI
echo ""
echo "[6/6] 安装 Open WebUI（聊天界面）..."

export HF_ENDPOINT=https://hf-mirror.com

if "$PYTHON" -c "import open_webui" 2>/dev/null; then
    echo "  [√] Open WebUI 已安装"
else
    echo "  正在安装 Open WebUI（需要几分钟，首次会下载模型）..."
    if "$PYTHON" -m pip install --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple open-webui 2>/dev/null; then
        echo "  [√] Open WebUI 安装完成"
    else
        echo "  [!] Open WebUI 安装失败（可能需要 Python 3.11+）"
        echo "  聊天界面暂不可用，可稍后手动安装:"
        echo "    $PYTHON -m pip install open-webui"
        WEBUI_SKIP=1
    fi
fi

if [ -z "$WEBUI_SKIP" ]; then
    # 注册 Open WebUI 服务
    WEBUI_SERVICE_FILE="/etc/systemd/system/geometry-ai-webui.service"
    cat > "$WEBUI_SERVICE_FILE" << SVCEOF
[Unit]
Description=Geometry AI WebUI (Open WebUI)
After=network.target geometry-ai.service

[Service]
Type=simple
User=$SERVICE_USER
ExecStart=$PYTHON -m open_webui.main
Restart=always
RestartSec=5
Environment=HF_ENDPOINT=https://hf-mirror.com
Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1
Environment=OPENAI_API_KEYS=not-needed

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable geometry-ai-webui
    systemctl start geometry-ai-webui
    echo "  [√] Open WebUI 已启动（端口 8080）"
fi

echo ""
echo "  ========================================================"
echo "  [√] 安装完成！"
echo "  ========================================================"
echo ""
echo "    管理界面: http://localhost:5000/admin"
echo "    聊天界面: http://localhost:8080"
echo ""
echo "    停止服务: sudo systemctl stop geometry-ai"
echo "    启动服务: sudo systemctl start geometry-ai"
echo "    查看日志: sudo journalctl -u geometry-ai -f"
echo "    卸载服务: bash uninstall_linux.sh"
echo ""
