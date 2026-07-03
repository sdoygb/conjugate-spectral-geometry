#!/bin/bash
# Geometry AI Server - Ubuntu 全自动安装
# 一条命令搞定，无需手动操作
set -e

BANNER='
  ============================================================
      Geometry AI Server - Ubuntu 全自动安装
      一条命令搞定，无需手动操作
  ============================================================
'
echo "$BANNER"

if [ "$EUID" -ne 0 ]; then
    echo "[!] 请使用 sudo 运行: sudo bash install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="/usr/local/geometry-ai"

# ============================================================
# 提前输入 Key
# ============================================================
echo ""
echo "请在安装前准备好以下 Key（直接回车可跳过，安装后手动配置）:"
echo ""

read -p "  输入 DeepSeek API Key (必填): " DEEPSEEK_KEY
read -p "  输入 SiliconFlow API Key (可选): " SILICONFLOW_KEY

echo ""

# ============================================================
# Step 1: 确保 Python 3.10+
# ============================================================
echo "[1/5] 检查 Python 环境..."

PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")" 2>/dev/null)
        major="${ver%%.*}"
        minor="${ver##*.}"
        if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  Python 版本过低，通过 PPA 安装 Python 3.11..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq 2>/dev/null || true
    apt-get install -y software-properties-common 2>/dev/null || true
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
    apt-get update -qq 2>/dev/null || true
    if apt-get install -y python3.11 python3.11-pip python3.11-venv 2>/dev/null; then
        PYTHON="python3.11"
    else
        apt-get install -y python3 python3-pip 2>/dev/null || true
        PYTHON="python3"
    fi
fi

if ! "$PYTHON" -m pip --version &>/dev/null; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$PYTHON"
fi

PYTHON_PATH="$(command -v "$PYTHON")"
update-alternatives --install /usr/bin/python3 python3 "$PYTHON_PATH" 100 2>/dev/null || true

PY_VER=$($PYTHON -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")" 2>/dev/null)
echo "  [ok] Python $PY_VER ($PYTHON_PATH)"

# ============================================================
# Step 2: 复制程序文件
# ============================================================
echo "[2/5] 复制程序文件..."
rm -rf "$APP_DIR" 2>/dev/null || true
cp -r "$SCRIPT_DIR/usr/local/geometry-ai" "/usr/local/"
mkdir -p "$APP_DIR/chroma_db" "$APP_DIR/articles" "$APP_DIR/logs" 2>/dev/null || true
chmod -R 755 "$APP_DIR"

# 写入 .env（包含用户输入的 Key）
if [ -n "$DEEPSEEK_KEY" ]; then
    sed -i "s|GAI_API_KEY=在此|GAI_API_KEY=$DEEPSEEK_KEY|" "$APP_DIR/.env.example"
fi
if [ -n "$SILICONFLOW_KEY" ]; then
    sed -i "s|SILICONFLOW_API_KEY=|SILICONFLOW_API_KEY=$SILICONFLOW_KEY|" "$APP_DIR/.env.example"
fi
cp "$APP_DIR/.env.example" "$APP_DIR/.env" 2>/dev/null || true

echo "  [ok] 文件已复制到 $APP_DIR"

# ============================================================
# Python 兼容性修复
# ============================================================
echo "  检查 Python 代码兼容性..."
$PYTHON -c "import ast; ast.parse(open('$APP_DIR/knowledge.py').read())" 2>/dev/null || {
    echo "  添加 Python 类型注解兼容声明..."
    for f in knowledge.py tools.py stream.py server.py models.py admin_routes.py share_routes.py config.py; do
        fp="$APP_DIR/$f"
        [ -f "$fp" ] || continue
        if ! head -1 "$fp" 2>/dev/null | grep -q "__future__"; then
            sed -i '1i from __future__ import annotations' "$fp"
        fi
    done
}

# ============================================================
# Step 3: 安装 Python 依赖
# ============================================================
echo "[3/5] 安装 Python 依赖..."

"$PYTHON" -m pip install --upgrade pip setuptools wheel -q 2>/dev/null || true

SQLITE_VER=$($PYTHON -c "import sqlite3; print(sqlite3.sqlite_version)" 2>/dev/null || echo "0.0.0")
SQLITE_MAJOR="${SQLITE_VER%%.*}"
SQLITE_MINOR_PART="${SQLITE_VER#*.}"
SQLITE_MINOR="${SQLITE_MINOR_PART%%.*}"

echo "  系统 sqlite3 版本: $SQLITE_VER"

MIRRORS=(
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://pypi.mirrors.ustc.edu.cn/simple/"
    "https://pypi.org/simple/"
)

pip_install() {
    local pkg="$1"
    for mirror in "${MIRRORS[@]}"; do
        if "$PYTHON" -m pip install -i "$mirror" --upgrade $pkg 2>/dev/null; then
            return 0
        fi
    done
    "$PYTHON" -m pip install --upgrade $pkg 2>/dev/null || return 1
}

if [ -f "$APP_DIR/requirements.txt" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        pip_install "$line" || true
    done < "$APP_DIR/requirements.txt"
fi

if [ "$SQLITE_MAJOR" -lt 3 ] || { [ "$SQLITE_MAJOR" -eq 3 ] && [ "$SQLITE_MINOR" -lt 35 ]; }; then
    echo "  sqlite3 版本低于 3.35，安装 pysqlite3-binary..."
    pip_install "pysqlite3-binary" || pip_install "pysqlite3-binary>=0.4.7" || true
    if ! grep -q "_fix_sqlite" "$APP_DIR/config.py" 2>/dev/null; then
        sed -i '1i from _fix_sqlite import *' "$APP_DIR/config.py"
    fi
fi

echo "  [ok] 依赖安装完成"

# ============================================================
# Step 4: 注册 systemd 服务
# ============================================================
echo "[4/5] 注册 systemd 服务..."

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

# 启动前验证 SiliconFlow Key 是否有效
echo "[4.5/6] 验证 SiliconFlow API Key..."
SF_KEY=$(grep '^SILICONFLOW_API_KEY=' "$APP_DIR/.env" 2>/dev/null | cut -d= -f2)
if [ -n "$SF_KEY" ]; then
    TEST_RESP=$(curl -s -X POST https://api.siliconflow.cn/v1/embeddings         -H "Authorization: Bearer $SF_KEY"         -H "Content-Type: application/json"         -d '{"model":"BAAI/bge-large-zh-v1.5","input":["test"]}' 2>/dev/null || echo '{"error":"connection failed"}')
    if echo "$TEST_RESP" | grep -q '"error"'; then
        echo "  [!] 警告: SiliconFlow API Key 无效或余额不足"
        echo "     Embeddeding 将无法使用，请检查 Key"
        echo "     Key 文件: $APP_DIR/.env"
        echo "     POST 测试响应: $TEST_RESP"
    else
        echo "  [ok] SiliconFlow API Key 有效"
    fi
else
    echo "  [!] 警告: 未配置 SiliconFlow API Key"
fi

systemctl start geometry-ai || true

echo "  等待服务启动..."
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "  [ok] 服务已启动 (端口 5000)"
        break
    fi
    sleep 2
done

# ============================================================
# Step 5: 自动重建知识库索引
# ============================================================
echo "[5/6] 重建知识库索引..."
ARTICLE_COUNT=$(find "$APP_DIR/articles" -maxdepth 1 -name '*.md' | wc -l)
echo "  文章文件数: $ARTICLE_COUNT"
if [ "$ARTICLE_COUNT" -gt 0 ]; then
    curl -s -X POST http://localhost:5000/v1/index/rebuild 2>/dev/null &&         echo "  [ok] 知识库索引已重建" ||         echo "  [!] 索引重建请求已发送，索引可能需要几分钟"
fi

# ============================================================
# Step 6: 完成
# ============================================================
echo ""
echo "  ============================================================"
echo "  [ok] 安装完成！"
echo "  ============================================================"
echo ""
echo "  ▸ 管理页面: http://localhost:5000/admin"
echo "  ▸ 健康检查: http://localhost:5000/health"
echo ""
echo "  ▸ 配置目录: $APP_DIR/.env"
if [ -z "$DEEPSEEK_KEY" ]; then
    echo "  ▸ 注意: 你未输入 DeepSeek API Key"
    echo "    请执行: sudo nano $APP_DIR/.env"
    echo "    将 GAI_API_KEY=在此 改为你的 Key"
    echo "    然后: sudo systemctl restart geometry-ai"
fi
echo ""
echo "  ▸ 常用命令:"
echo "    状态: sudo systemctl status geometry-ai"
echo "    日志: sudo journalctl -u geometry-ai -f"
echo "    重启: sudo systemctl restart geometry-ai"
echo "    卸载: sudo bash $APP_DIR/uninstall.sh"
echo ""
