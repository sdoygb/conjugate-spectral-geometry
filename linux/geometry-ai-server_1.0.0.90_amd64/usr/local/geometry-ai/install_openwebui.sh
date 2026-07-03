#!/bin/bash
set -e
echo ""
echo "  Open WebUI 安装脚本"
echo ""
echo "1) Docker安装 (推荐)"
echo "2) pip安装"
echo "3) 跳过"
read -p "请选择 [1-3] (默认: 1): " c
c="${c:-1}"
if [ "$c" = "1" ]; then
    if ! command -v docker >/dev/null; then
        curl -fsSL https://get.docker.com | bash
    fi
    docker pull ghcr.io/open-webui/open-webui:main
    docker run -d -p 8080:8080 --name geometry-webui \        --restart unless-stopped \        -e OPENAI_API_BASE_URL=http://172.17.0.1:5000/v1 \        -e OPENAI_API_KEY=not-needed \        -v open-webui-data:/app/backend/data \        ghcr.io/open-webui/open-webui:main
    echo "[ok] Open WebUI: http://localhost:8080"
elif [ "$c" = "2" ]; then
    pip3 install open-webui
    echo "[ok] 运行: open-webui serve"
fi
