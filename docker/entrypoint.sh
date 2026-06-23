#!/bin/bash
# Geometry AI Server - Docker 启动脚本
set -e

# ============================================================
# 初始化配置
# ============================================================
ENV_FILE="/app/.env"

if [ ! -f "$ENV_FILE" ]; then
    if [ -n "$KIMI_API_KEY" ]; then
        # 从环境变量生成 .env
        cat > "$ENV_FILE" << EOF
# Geometry AI Server 配置（Docker 自动生成）
KIMI_API_KEY=${KIMI_API_KEY}
KIMI_BASE_URL=${KIMI_BASE_URL:-https://api.deepseek.com/v1}
KIMI_MODEL=${KIMI_MODEL:-deepseek-v4-pro}
KIMI_MODEL_LITE=${KIMI_MODEL_LITE:-deepseek-v4-flash}
KIMI_MODEL_VISION=${KIMI_MODEL_VISION:-deepseek-v4-flash}
KIMI_EMBEDDING_MODEL=${KIMI_EMBEDDING_MODEL:-deepseek-v4-flash}
EOF
        echo "[INIT] .env 已从环境变量生成"
    else
        # 生成空模板
        cat > "$ENV_FILE" << EOF
# Geometry AI Server 配置
# 请在 docker run 时通过 -e KIMI_API_KEY=你的key 传入
# 或直接编辑此文件后重启容器
KIMI_API_KEY=
KIMI_BASE_URL=https://api.deepseek.com/v1
KIMI_MODEL=deepseek-v4-pro
KIMI_MODEL_LITE=deepseek-v4-flash
KIMI_MODEL_VISION=deepseek-v4-flash
KIMI_EMBEDDING_MODEL=deepseek-v4-flash
EOF
        echo "[WARN] 未设置 KIMI_API_KEY，请在 docker run 时传入 -e KIMI_API_KEY=你的key"
    fi
fi

# ============================================================
# 启动 Geometry AI Server（后台）
# ============================================================
echo "[START] 启动 Geometry AI Server（端口 5000）..."
python server.py &
SERVER_PID=$!

# 等待 Server 启动
for i in $(seq 1 30); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo "[OK] Geometry AI Server 已启动"
        break
    fi
    sleep 1
done

# ============================================================
# 启动 Open WebUI（前台）
# ============================================================
echo "[START] 启动 Open WebUI（端口 8080）..."

# 查找 open-webui 命令
if command -v open-webui &>/dev/null; then
    exec open-webui serve
else
    exec python -m open_webui.main
fi
