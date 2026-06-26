#!/bin/bash
# Geometry AI Server - Linux 全自动安装
# 使用方法: sudo bash install_linux.sh
# 仅需一条命令，无需手动安装任何依赖

echo ""
echo "  ========================================================"
echo "      Geometry AI Server - Linux 全自动安装"
echo "      一条命令搞定，无需手动安装任何东西"
echo "  ========================================================"
echo ""

# 检测 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash install_linux.sh"
    exit 1
fi

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$INSTALL_DIR/app"
SERVICE_USER="${SUDO_USER:-root}"

# ============================================================
# Step 1: 确保 Python 3.10+ 可用
# ============================================================
echo "[1/6] 准备 Python 3.11 环境..."

PYTHON=""

# 先找系统已有的 Python 3.10+
for cmd in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        major=${ver%%.*}
        minor=${ver##*.}
        if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  系统未安装 Python 3.10+，正在自动安装..."

    if command -v apt-get &>/dev/null; then
        # Ubuntu/Debian
        echo "  检测到 apt-get，正在安装 Python 3.11..."

        # 尝试方法1: add-apt-repository + PPA（完全非交互）
        PPADONE=0
        export DEBIAN_FRONTEND=noninteractive
        if command -v add-apt-repository &>/dev/null; then
            apt-get install -y software-properties-common 2>/dev/null || true
            add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null && apt-get update -qq 2>/dev/null && PPADONE=1
        fi
        unset DEBIAN_FRONTEND

        if [ "$PPADONE" -eq 1 ]; then
            if apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip; then
                PYTHON="python3.11"
            fi
        fi

        # 尝试方法2: 手动添加 deadsnakes 源
        if [ -z "$PYTHON" ]; then
            echo "  PPA 不可用，尝试手动添加 deadsnakes 源..."
            . /etc/os-release 2>/dev/null
            CODENAME="${VERSION_CODENAME:-}"
            if [ -z "$CODENAME" ] && command -v lsb_release &>/dev/null; then
                CODENAME=$(lsb_release -cs 2>/dev/null)
            fi
            if [ -z "$CODENAME" ]; then
                CODENAME="focal"
            fi
            echo "deb http://archive.ubuntu.com/ubuntu $CODENAME universe" > /etc/apt/sources.list.d/deadsnakes.list
            echo "deb http://archive.ubuntu.com/ubuntu $CODENAME-updates universe" >> /etc/apt/sources.list.d/deadsnakes.list
            apt-get update
            if apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip; then
                PYTHON="python3.11"
            fi
        fi

        # 尝试方法3: 用系统自带的 python3（3.10+ 也可以）
        if [ -z "$PYTHON" ]; then
            echo "  deadsnakes 不可用，检查系统自带 Python..."
            if command -v python3 &>/dev/null; then
                SYS_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
                SYS_MAJOR=$(echo "$SYS_VER" | cut -d. -f1)
                SYS_MINOR=$(echo "$SYS_VER" | cut -d. -f2)
                if [ "$SYS_MAJOR" -eq 3 ] && [ "$SYS_MINOR" -ge 10 ]; then
                    echo "  使用系统 Python $SYS_VER（满足最低要求 3.10+）"
                    PYTHON="python3"
                fi
            fi
        fi

        # 尝试方法4: 用 pyenv 编译安装
        if [ -z "$PYTHON" ]; then
            echo "  系统无合适 Python，正在用 pyenv 编译安装 3.11（需要几分钟）..."
            apt-get install -y make build-essential libssl-dev zlib1g-dev \
                libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
                libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev 2>/dev/null
            curl -sSL https://pyenv.run 2>/dev/null | bash
            export PYENV_ROOT="$HOME/.pyenv"
            export PATH="$PYENV_ROOT/bin:$PATH"
            eval "$(pyenv init -)" 2>/dev/null
            pyenv install 3.11 2>/dev/null
            pyenv global 3.11 2>/dev/null
            PYTHON="$PYENV_ROOT/shims/python3"
        fi

    elif command -v dnf &>/dev/null; then
        echo "  检测到 dnf，正在安装 Python 3.11..."
        dnf install -y python3.11 python3.11-pip python3.11-devel || \
        dnf install -y python3.12 python3.12-pip python3.12-devel || \
        dnf install -y python3 python3-pip python3-devel
        PYTHON="python3.11"

    elif command -v yum &>/dev/null; then
        echo "  检测到 yum，正在安装 Python..."
        yum install -y epel-release || true
        yum install -y python3 python3-pip python3-devel
        PYTHON="python3"

    elif command -v apk &>/dev/null; then
        echo "  检测到 apk，正在安装 Python 3.11..."
        apk add --no-cache python3.11 py3-pip
        PYTHON="python3.11"

    else
        echo "[!] 无法识别的包管理器，请手动安装 Python 3.10+"
        echo "    Ubuntu/Debian: sudo apt-get install python3.11"
        echo "    Fedora: sudo dnf install python3.11"
        echo "    其他: https://www.python.org/downloads/"
        exit 1
    fi
fi

# 验证 Python 可用
if ! command -v "$PYTHON" &>/dev/null; then
    echo "[!] Python 安装失败，请手动安装 Python 3.10+ 后重试"
    exit 1
fi

PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)" 2>/dev/null)
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)" 2>/dev/null)

if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 10 ]; then
    echo "[!] Python 版本过低 ($PY_VER)，需要 3.10+"
    echo "    请手动安装: sudo apt-get install python3.11"
    exit 1
fi

echo "  [√] Python $PY_VER ($PYTHON)"

# ============================================================
# Step 2: 安装 Python 依赖
# ============================================================
echo ""
echo "[2/6] 安装 Python 依赖..."

# 检查并升级系统 sqlite3（ChromaDB 要求 >= 3.35.0）
echo "  检查系统 sqlite3 版本..."
SQLITE_VER=$(sqlite3 --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
if [ -n "$SQLITE_VER" ]; then
    SQLITE_MAJOR=$(echo "$SQLITE_VER" | cut -d. -f1)
    SQLITE_MINOR=$(echo "$SQLITE_VER" | cut -d. -f2)
    if [ "$SQLITE_MAJOR" -lt 3 ] || { [ "$SQLITE_MAJOR" -eq 3 ] && [ "$SQLITE_MINOR" -lt 35 ]; }; then
        echo "  sqlite3 版本过低 ($SQLITE_VER)，正在升级..."
        if command -v apt-get &>/dev/null; then
            apt-get install -y -qq libsqlite3-dev wget 2>/dev/null
            # 从源码编译安装新版 sqlite3
            SQLITE_URL="https://www.sqlite.org/2024/sqlite-autoconf-3450000.tar.gz"
            wget -q "$SQLITE_URL" -O /tmp/sqlite3.tar.gz 2>/dev/null && \
            cd /tmp && tar xzf sqlite3.tar.gz && cd sqlite-autoconf-3450000 && \
            ./configure --prefix=/usr/local && make -j$(nproc) && make install && \
            ldconfig && \
            echo "  [√] sqlite3 已升级到 3.45.0"
        elif command -v yum &>/dev/null; then
            yum install -y sqlite-devel wget 2>/dev/null
            SQLITE_URL="https://www.sqlite.org/2024/sqlite-autoconf-3450000.tar.gz"
            wget -q "$SQLITE_URL" -O /tmp/sqlite3.tar.gz 2>/dev/null && \
            cd /tmp && tar xzf sqlite3.tar.gz && cd sqlite-autoconf-3450000 && \
            ./configure --prefix=/usr/local && make -j$(nproc) && make install && \
            ldconfig && \
            echo "  [√] sqlite3 已升级到 3.45.0"
        fi
    else
        echo "  [√] sqlite3 版本 $SQLITE_VER（满足要求）"
    fi
else
    echo "  未检测到 sqlite3，将使用 pysqlite3-binary"
fi
# 升级 pip
"$PYTHON" -m pip install --disable-pip-version-check --upgrade pip 2>&1 | tail -1 || true

# 安装依赖
echo "  正在安装依赖（可能需要几分钟）..."
"$PYTHON" -m pip install --disable-pip-version-check \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r "$APP_DIR/requirements.txt" 2>&1 | tail -3

echo "  [√] 依赖安装完成"

# ============================================================
# Step 3: 配置 API Key
# ============================================================
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

# ============================================================
# Step 4: 停止旧服务
# ============================================================
echo ""
echo "[4/6] 停止旧服务..."
systemctl stop geometry-ai-webui 2>/dev/null || true
systemctl stop geometry-ai 2>/dev/null || true
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# 清理旧版 service 文件（确保使用最新配置）
echo "  清理旧配置..."
rm -f /etc/systemd/system/geometry-ai.service 2>/dev/null
rm -f /etc/systemd/system/geometry-ai-webui.service 2>/dev/null
systemctl daemon-reload 2>/dev/null

# ============================================================
# Step 5: 注册 systemd 服务并启动
# ============================================================
echo ""
echo "[5/6] 注册 systemd 服务..."

# 获取 python 完整路径
PYTHON_PATH=$(command -v "$PYTHON" 2>/dev/null)

if [ -z "$PYTHON_PATH" ]; then
    echo "[!] 找不到 Python 路径"
    exit 1
fi

cat > /etc/systemd/system/geometry-ai.service << SVCEOF
[Unit]
Description=Geometry AI Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON_PATH $APP_DIR/server.py
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
STARTED=0
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "  [√] Geometry AI Server 已启动（端口 5000）"
        STARTED=1
        break
    fi
    sleep 2
done
if [ "$STARTED" -eq 0 ]; then
    echo "  [!] 服务启动较慢，请稍后检查: sudo systemctl status geometry-ai"
fi

# ============================================================
# Step 6: 安装 Open WebUI（可选）
# ============================================================
echo ""
echo "[6/6] 安装 Open WebUI（聊天界面）..."

export HF_ENDPOINT=https://hf-mirror.com

if "$PYTHON" -c "import open_webui" 2>/dev/null; then
    echo "  [√] Open WebUI 已安装"
else
    echo "  正在安装 Open WebUI（首次需要几分钟下载模型）..."
    if "$PYTHON" -m pip install --disable-pip-version-check \
        -i https://pypi.tuna.tsinghua.edu.cn/simple open-webui 2>&1 | tail -3 | grep -qi "success"; then
        echo "  [√] Open WebUI 安装完成"
    else
        echo "  [!] Open WebUI 安装失败，聊天界面暂不可用"
        echo "  可稍后手动安装: $PYTHON -m pip install open-webui"
        echo "  或使用 Docker: docker run -d -p 8080:8080 ghcr.io/open-webui/open-webui:main"
        WEBUI_SKIP=1
    fi
fi

if [ -z "${WEBUI_SKIP:-}" ]; then
    # 生成随机 WEBUI_SECRET_KEY
    WEBUI_SECRET=$("$PYTHON" -c "import secrets; print(secrets.token_hex(32))")
    cat > /etc/systemd/system/geometry-ai-webui.service << SVCEOF
[Unit]
Description=Geometry AI WebUI (Open WebUI)
After=network.target geometry-ai.service

[Service]
Type=simple
User=$SERVICE_USER
ExecStart=$PYTHON_PATH -m open_webui serve
Restart=always
RestartSec=5
Environment=HF_ENDPOINT=https://hf-mirror.com
Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1
Environment=OPENAI_API_KEYS=not-needed
Environment=WEBUI_SECRET_KEY=$WEBUI_SECRET
Environment=WEBUI_HOST=0.0.0.0
Environment=WEBUI_PORT=8080

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable geometry-ai-webui
    systemctl start geometry-ai-webui
    echo "  [√] Open WebUI 已启动（端口 8080）"
fi

# ============================================================
# 完成
# ============================================================
echo ""
echo "  ========================================================"
echo "  [√] 安装完成！"
echo "  ========================================================"
echo ""
echo "    管理界面: http://localhost:5000/admin"
if [ -z "${WEBUI_SKIP:-}" ]; then
echo "    聊天界面: http://localhost:8080"
fi
echo ""
echo "    停止服务: sudo systemctl stop geometry-ai"
echo "    启动服务: sudo systemctl start geometry-ai"
echo "    查看日志: sudo journalctl -u geometry-ai -f"
echo "    卸载服务: sudo bash uninstall_linux.sh"
echo ""
