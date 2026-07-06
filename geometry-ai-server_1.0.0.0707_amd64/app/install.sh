#!/bin/bash
# Geometry AI Server - Ubuntu 安装脚本 v1.0.0.0707
# 不用 set -e，apt 等命令可能返回非零但实际成功

if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash install.sh"
    exit 1
fi

echo ""
echo "  ========================================================="
echo "      Geometry AI Server v1.0.0.0707 - Ubuntu 安装"
echo "  ========================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="/usr/local/geometry-ai"

read -p "  输入 DeepSeek API Key (必填): " DEEPSEEK_KEY
read -p "  输入 SiliconFlow API Key (可选,直接回车跳过): " SILICONFLOW_KEY
# Step 1: Python 3.11+
echo "[1/6] 检查 Python 环境（需要 3.11+）..."
PYTHON=""
MIN_VER=11
for cmd in python3.13 python3.12 python3.11; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c "import sys; v=sys.version_info; print(str(v.major)+chr(46)+str(v.minor))" 2>/dev/null)
        if [ "${ver%%.*}" = "3" ] && [ "${ver##*.}" -ge "$MIN_VER" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done
if [ -z "$PYTHON" ]; then
    echo "  当前 Python 版本过低，尝试安装 Python 3.11..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null
    apt-get update
    apt-get install -y python3.11 python3.11-pip python3.11-venv python3.11-dev
    if ! command -v python3.11 &>/dev/null; then
        echo "  PPA 安装失败，尝试从源码编译 Python 3.11..."
        apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-compat-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
        cd /tmp
        wget -q https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
        tar xzf Python-3.11.9.tgz
        cd Python-3.11.9
        ./configure --prefix=/usr/local --enable-optimizations --with-ensurepip=install > /dev/null 2>&1
        make -j$(nproc) > /dev/null 2>&1
        make altinstall > /dev/null 2>&1
        cd /tmp
        rm -rf Python-3.11.9 Python-3.11.9.tgz
    fi
    if command -v python3.11 &>/dev/null; then
        PYTHON="python3.11"
        echo "  [ok] Python 3.11 安装成功"
    else
        echo "[!] Python 3.11 安装失败"
        echo "    请手动安装: https://docs.python.org/3/using/unix.html#building-python"
        exit 1
    fi
fi
PYTHON_PATH="$(command -v $PYTHON)"
PY_VER=$($PYTHON -c "import sys; print(str(sys.version_info.major)+chr(46)+str(sys.version_info.minor))")
echo "  Python: $PYTHON $PY_VER ($PYTHON_PATH)"
if [ "${PY_VER##*.}" -lt "$MIN_VER" ]; then
    echo "[!] 需要 Python 3.11+，当前 $PY_VER"
    exit 1
fi

# Step 2: 复制文件
echo "[2/6] 安装程序文件..."
rm -rf "$APP_DIR" 2>/dev/null || true
cp -r "$SCRIPT_DIR/app" "$APP_DIR"
mkdir -p "$APP_DIR/chroma_db" "$APP_DIR/logs"
chmod -R 755 "$APP_DIR"

# 写入 .env
if [ -n "$DEEPSEEK_KEY" ]; then
    sed -i "s|GAI_API_KEY=在此|GAI_API_KEY=$DEEPSEEK_KEY|" "$APP_DIR/.env.example"
fi
if [ -n "$SILICONFLOW_KEY" ]; then
    sed -i "s|SILICONFLOW_API_KEY=|SILICONFLOW_API_KEY=$SILICONFLOW_KEY|" "$APP_DIR/.env.example"
fi
cp "$APP_DIR/.env.example" "$APP_DIR/.env"
echo "  [ok] 文件已安装到 $APP_DIR"

# Step 3: pip 依赖
echo "[3/6] 安装 Python 依赖..."
MIRRORS="https://mirrors.aliyun.com/pypi/simple/ https://pypi.tuna.tsinghua.edu.cn/simple/"
for mirror in $MIRRORS; do
    $PYTHON -m pip install -i $mirror -r "$APP_DIR/requirements.txt" -q 2>/dev/null && break
done
echo "  [ok] 依赖安装完成"

# Step 4: systemd 服务
echo "[4/6] 注册 systemd 服务..."
cat > /etc/systemd/system/geometry-ai.service << SERVICEEOF
[Unit]
Description=Geometry AI Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$PYTHON_PATH $APP_DIR/server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEEOF
systemctl daemon-reload
systemctl enable geometry-ai
systemctl start geometry-ai

echo "  等待服务启动..."
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "  [ok] 服务已启动 (端口 5000)"
        break
    fi
    sleep 2
done

# Step 5: 重建索引
echo "[6/6] 重建知识库索引..."
ARTICLE_COUNT=$(find "$APP_DIR/articles" -maxdepth 1 -name '*.md' | wc -l)
echo "  文章文件数: $ARTICLE_COUNT"
if [ "$ARTICLE_COUNT" -gt 0 ]; then
    RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)
    if echo "$RESP" | grep -q '"success": true'; then
        echo "  [ok] 知识库索引已重建"
    else
        echo "  [!] 索引重建请求已发送（可能需要几分钟）"
        echo "  响应: $RESP"
        echo "  手动重建: sudo bash $APP_DIR/fix_index.sh"
    fi
fi

echo ""
echo "  ========================================================="
echo "  [ok] 安装完成！"
echo "  ========================================================="
echo ""
echo "  管理页面: http://localhost:5000/admin"
echo "  健康检查: http://localhost:5000/health"
echo "  配置文件: $APP_DIR/.env"
echo ""
echo "  状态: sudo systemctl status geometry-ai"
echo "  日志: sudo journalctl -u geometry-ai -f"
echo "  卸载: sudo bash $APP_DIR/uninstall.sh"
