#!/bin/bash
# Geometry AI Server - Ubuntu 安装脚本 v1.0.0.0707
set -e

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

# Step 1: Python
echo "[1/5] 检查 Python 环境..."
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c "import sys; print(sys.version_info.major .sys.version_info.minor)" 2>/dev/null)
        if [ "${ver%%.*}" = "3" ] && [ "${ver##*.}" -ge 10 ] 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done
if [ -z "$PYTHON" ]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq 2>/dev/null
    apt-get install -y python3 python3-pip 2>/dev/null || true
    PYTHON="python3"
fi
PYTHON_PATH="$(command -v $PYTHON)"
echo "  Python: $PYTHON ($($PYTHON --version 2>&1))"

# Step 2: 复制文件
echo "[2/5] 安装程序文件..."
rm -rf "$APP_DIR" 2>/dev/null || true
cp -r "$SCRIPT_DIR/usr/local/geometry-ai" "/usr/local/"
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
echo "[3/5] 安装 Python 依赖..."
MIRRORS="https://mirrors.aliyun.com/pypi/simple/ https://pypi.tuna.tsinghua.edu.cn/simple/"
for mirror in $MIRRORS; do
    $PYTHON -m pip install -i $mirror -r "$APP_DIR/requirements.txt" -q 2>/dev/null && break
done
echo "  [ok] 依赖安装完成"

# Step 4: systemd 服务
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
echo "[5/5] 重建知识库索引..."
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
