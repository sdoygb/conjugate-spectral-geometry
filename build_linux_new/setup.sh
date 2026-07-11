#!/bin/bash
# ==============================================================================
# GeometryAI 子AI 智能安装/升级脚本
# 自动检测：有旧版则升级，无旧版则全新安装
#
# 用法:
#   sudo bash setup.sh                    # 安装到 /opt/geometry-ai
#   sudo bash setup.sh /home/user/my-ai   # 指定目录（升级或安装）
#   sudo INSTALL_DIR=/home/user/my-ai bash setup.sh  # 同上
# ==============================================================================

set -e

# ==================== 配置区 ====================
SERVICE_NAME="geometry-ai"
MASTER_AI_URL="http://192.168.1.2:5001"
MASTER_AI_TOKEN="master-ai-verify"
SUB_AI_PORT=5000
PYTHON_VERSION="python3"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 安装目录：优先用命令行参数，其次自动检测，最后默认值
INSTALL_DIR="${1:-}"

# ==================== 颜色输出 ====================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
step()  { echo -e "${BLUE}>>>${NC} $1"; }

if [ "$EUID" -ne 0 ]; then exec sudo bash "$0" "$@"; fi

# ==================== 自动检测旧版目录 ====================
if [ -z "$INSTALL_DIR" ]; then
    step "搜索旧版安装..."
    if systemctl cat "$SERVICE_NAME" &>/dev/null; then
        SVC_DIR=$(systemctl cat "$SERVICE_NAME" 2>/dev/null | grep "WorkingDirectory=" | head -1 | cut -d= -f2)
        if [ -n "$SVC_DIR" ] && [ -f "$SVC_DIR/server.py" ]; then
            INSTALL_DIR="$SVC_DIR"; info "从systemd检测到: $INSTALL_DIR"
        fi
    fi
    if [ -z "$INSTALL_DIR" ]; then
        for candidate in /opt/geometry-ai /opt/geometry_ai /home/*/geometry-ai /home/*/app /srv/geometry-ai /usr/local/geometry-ai; do
            for dir in $candidate; do
                if [ -d "$dir" ] && [ -f "$dir/server.py" ] && [ -f "$dir/master_client.py" ]; then
                    INSTALL_DIR="$dir"; info "搜索到旧版: $INSTALL_DIR"; break 2
                fi
            done
        done
    fi
    if [ -z "$INSTALL_DIR" ]; then
        INSTALL_DIR="/opt/geometry-ai"
        warn "未找到旧版，将全新安装到: $INSTALL_DIR"
    fi
fi

echo ""; echo "  目标目录: $INSTALL_DIR"; echo "  主库AI:   $MASTER_AI_URL"; echo ""

# ==================== 检测模式 ====================
IS_UPGRADE=false
if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/server.py" ]; then
    IS_UPGRADE=true; step "检测到旧版 → 升级模式"
else
    step "未检测到旧版 → 全新安装模式"
fi

# ==================== 全新安装 ====================
if [ "$IS_UPGRADE" = false ]; then
    step "1/6 检查系统环境..."
    PKG_MGR=""
    if command -v apt-get &>/dev/null; then PKG_MGR="apt"
    elif command -v dnf &>/dev/null; then PKG_MGR="dnf"
    elif command -v yum &>/dev/null; then PKG_MGR="yum"
    else error "不支持的发行版"; exit 1
    fi
    info "包管理器: $PKG_MGR"

    step "2/6 安装系统依赖..."
    case $PKG_MGR in
        apt) apt-get update -qq; apt-get install -y -qq python3 python3-pip python3-venv curl git 2>/dev/null ;;
        dnf|yum) $PKG_MGR install -y -q python3 python3-pip curl git 2>/dev/null ;;
    esac
    info "系统依赖安装完成"

    step "3/6 部署文件..."
    mkdir -p "$INSTALL_DIR"
    SRC="$SCRIPT_DIR/app"
    for f in server.py config.py master_client.py knowledge.py models.py prompts.py tools.py stream.py admin_routes.py share_routes.py version.py start.py auto_teach.py; do
        [ -f "$SRC/$f" ] && cp "$SRC/$f" "$INSTALL_DIR/"
    done
    for f in jieba_dict.txt requirements.txt; do
        [ -f "$SRC/$f" ] && cp "$SRC/$f" "$INSTALL_DIR/"
    done
    for d in articles templates; do
        [ -d "$SRC/$d" ] && cp -r "$SRC/$d" "$INSTALL_DIR/"
    done
    info "文件部署完成"

    step "4/6 创建虚拟环境并安装依赖..."
    $PYTHON_VERSION -m venv "$INSTALL_DIR/venv"
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q 2>&1 | tail -3
    info "依赖安装完成"

    step "5/6 生成配置..."
    cat > "$INSTALL_DIR/.env" << ENVEOF
MASTER_AI_URL=$MASTER_AI_URL
MASTER_AI_TOKEN=$MASTER_AI_TOKEN
GAI_API_KEY=在此填入你的DeepSeek API Key
GAI_BASE_URL=https://api.deepseek.com/v1
GAI_MODEL=deepseek-v4-pro
GAI_MODEL_LITE=deepseek-v4-flash
GAI_EMBEDDING_MODEL=deepseek-v4-flash
SILICONFLOW_API_KEY=
GAI_EMBEDDING_MODE=siliconflow
ENVEOF
    info "配置文件已生成: $INSTALL_DIR/.env"
    info "请编辑 $INSTALL_DIR/.env 填入你的 GAI_API_KEY"

    step "6/6 注册服务并启动..."
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SVCEOF
[Unit]
Description=Geometry AI Sub-Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 server.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=MASTER_AI_URL=${MASTER_AI_URL}
Environment=MASTER_AI_TOKEN=${MASTER_AI_TOKEN}
LimitNOFILE=65536
[Install]
WantedBy=multi-user.target
SVCEOF
    systemctl daemon-reload; systemctl enable "$SERVICE_NAME"; systemctl start "$SERVICE_NAME"
    info "子AI服务已启动"

    # 安装 Open WebUI
    if ! "$INSTALL_DIR/venv/bin/python3" -c "import open_webui" 2>/dev/null; then
        warn "安装 PyTorch (CPU 版，无 CUDA)..."
        "$INSTALL_DIR/venv/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | tail -3 || true
        warn "安装 Open WebUI..."
        "$INSTALL_DIR/venv/bin/pip" install open-webui -q 2>&1 | tail -3 || true
    fi
    if "$INSTALL_DIR/venv/bin/python3" -c "import open_webui" 2>/dev/null; then
        WEBUI_SECRET=$("$INSTALL_DIR/venv/bin/python3" -c "import secrets; print(secrets.token_hex(32))")
        cat > "/etc/systemd/system/${SERVICE_NAME}-webui.service" << SVCEOF
[Unit]
Description=Geometry AI WebUI (Open WebUI)
After=network.target ${SERVICE_NAME}.service
[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 -m open_webui serve
Restart=always
RestartSec=5
Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1
Environment=OPENAI_API_KEYS=not-needed
Environment=WEBUI_SECRET_KEY=$WEBUI_SECRET
Environment=WEBUI_NAME=Geometry AI
Environment=WEBUI_PORT=8080
[Install]
WantedBy=multi-user.target
SVCEOF
        systemctl daemon-reload; systemctl enable "${SERVICE_NAME}-webui" 2>/dev/null; systemctl start "${SERVICE_NAME}-webui" 2>/dev/null || true
        info "Open WebUI 已启动 (端口 8080)"
    fi

# ==================== 升级 ====================
else
    step "1/4 备份..."
    [ -f "$INSTALL_DIR/.env" ] && cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.backup"
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    info "已备份 .env 并停止服务"

    step "2/4 更新源码..."
    SRC="$SCRIPT_DIR/app"
    for f in server.py config.py master_client.py knowledge.py models.py prompts.py tools.py stream.py admin_routes.py share_routes.py version.py start.py auto_teach.py; do
        [ -f "$SRC/$f" ] && cp "$SRC/$f" "$INSTALL_DIR/"
    done
    for f in requirements.txt; do
        [ -f "$SRC/$f" ] && cp "$SRC/$f" "$INSTALL_DIR/"
    done
    if [ -d "$SRC/articles" ]; then
        rm -rf "$INSTALL_DIR/articles_old" 2>/dev/null
        mv "$INSTALL_DIR/articles" "$INSTALL_DIR/articles_old" 2>/dev/null || true
        cp -r "$SRC/articles" "$INSTALL_DIR/"
        info "知识库已更新（旧版备份在articles_old/）"
    fi
    [ -d "$SRC/templates" ] && cp -r "$SRC/templates" "$INSTALL_DIR/"
    info "源码更新完成"

    step "3/4 检查依赖..."
    PIP="$INSTALL_DIR/venv/bin/pip"
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        python3 -m venv "$INSTALL_DIR/venv"
        "$PIP" install --upgrade pip -q
    fi
    # 带超时的 pip 安装（1分钟超时，防止网络卡死）
    timeout 60 "$PIP" install --default-timeout=30 -r "$INSTALL_DIR/requirements.txt" 2>&1 || {
        warn "pip安装超时或失败，重试一次..."
        timeout 60 "$PIP" install --default-timeout=60 -i https://pypi.tuna.tsinghua.edu.cn/simple -r "$INSTALL_DIR/requirements.txt" 2>&1 || {
            warn "pip安装失败，可手动执行: $PIP install -r $INSTALL_DIR/requirements.txt"
            info "继续启动服务..."
        }
    }
    info "依赖检查完成"

    step "4/4 恢复配置并启动..."
    if [ -f "$INSTALL_DIR/.env" ]; then
        info "配置文件已存在: $INSTALL_DIR/.env"
    elif [ -f "$INSTALL_DIR/.env.backup" ]; then
        if ! grep -q "MASTER_AI_URL" "$INSTALL_DIR/.env.backup"; then
            echo "" >> "$INSTALL_DIR/.env.backup"
            echo "MASTER_AI_URL=$MASTER_AI_URL" >> "$INSTALL_DIR/.env.backup"
            echo "MASTER_AI_TOKEN=$MASTER_AI_TOKEN" >> "$INSTALL_DIR/.env.backup"
        fi
        mv "$INSTALL_DIR/.env.backup" "$INSTALL_DIR/.env"
        info "已从备份恢复.env"
    else
        # 没有 .env 也没有备份 → 生成新的
        warn "未找到 .env 或备份，生成默认配置..."
        cat > "$INSTALL_DIR/.env" << ENVEOF
MASTER_AI_URL=$MASTER_AI_URL
MASTER_AI_TOKEN=$MASTER_AI_TOKEN
GAI_API_KEY=在此填入你的DeepSeek API Key
GAI_BASE_URL=https://api.deepseek.com/v1
GAI_MODEL=deepseek-v4-pro
GAI_MODEL_LITE=deepseek-v4-flash
GAI_EMBEDDING_MODEL=deepseek-v4-flash
SILICONFLOW_API_KEY=
GAI_EMBEDDING_MODE=siliconflow
ENVEOF
        info "已生成默认配置: $INSTALL_DIR/.env"
        warn "请编辑 $INSTALL_DIR/.env 填入 GAI_API_KEY"
    fi
    info "配置文件: $INSTALL_DIR/.env"
    # 重写 systemd 服务文件（确保使用 venv）
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SVCEOF
[Unit]
Description=Geometry AI Sub-Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 server.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=MASTER_AI_URL=${MASTER_AI_URL}
Environment=MASTER_AI_TOKEN=${MASTER_AI_TOKEN}
LimitNOFILE=65536
[Install]
WantedBy=multi-user.target
SVCEOF
    systemctl daemon-reload
    systemctl start "$SERVICE_NAME"
    info "子AI服务已重启"

    # 安装/更新 Open WebUI
    if ! "$INSTALL_DIR/venv/bin/python3" -c "import open_webui" 2>/dev/null; then
        warn "安装 PyTorch (CPU 版)..."
        "$INSTALL_DIR/venv/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | tail -3 || true
        warn "安装 Open WebUI..."
        "$INSTALL_DIR/venv/bin/pip" install open-webui -q 2>&1 | tail -3 || true
    fi
    if "$INSTALL_DIR/venv/bin/python3" -c "import open_webui" 2>/dev/null; then
        WEBUI_SECRET=$("$INSTALL_DIR/venv/bin/python3" -c "import secrets; print(secrets.token_hex(32))")
        cat > "/etc/systemd/system/${SERVICE_NAME}-webui.service" << SVCEOF
[Unit]
Description=Geometry AI WebUI (Open WebUI)
After=network.target ${SERVICE_NAME}.service
[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 -m open_webui serve
Restart=always
RestartSec=5
Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1
Environment=OPENAI_API_KEYS=not-needed
Environment=WEBUI_SECRET_KEY=$WEBUI_SECRET
Environment=WEBUI_NAME=Geometry AI
Environment=WEBUI_PORT=8080
[Install]
WantedBy=multi-user.target
SVCEOF
        systemctl daemon-reload; systemctl enable "${SERVICE_NAME}-webui" 2>/dev/null; systemctl start "${SERVICE_NAME}-webui" 2>/dev/null || true
        info "Open WebUI 已启动 (端口 8080)"
    fi
fi

# ==================== 健康检查 ====================
echo ""; sleep 5
if curl -s --max-time 10 "http://localhost:$SUB_AI_PORT/health" | grep -q "ok"; then
    info "健康检查通过!"
else
    warn "服务启动中... journalctl -u $SERVICE_NAME -f"
fi

echo ""
if curl -s --max-time 5 "$MASTER_AI_URL/health" | grep -q "ok"; then
    info "主库AI连接正常 ($MASTER_AI_URL)"
else
    warn "无法连接主库AI ($MASTER_AI_URL)"
fi

echo ""
echo "=========================================="
if [ "$IS_UPGRADE" = true ]; then
    echo -e "${GREEN}  GeometryAI 子AI 升级完成!${NC}"
else
    echo -e "${GREEN}  GeometryAI 子AI 安装完成!${NC}"
fi
echo "=========================================="
echo ""
echo "  安装目录:   $INSTALL_DIR"
echo "  配置文件:   $INSTALL_DIR/.env"
echo "  主库AI:     $MASTER_AI_URL"
echo "  子AI端口:   $SUB_AI_PORT"
echo "  WebUI:      http://localhost:8080"
echo "  服务: systemctl status $SERVICE_NAME"
echo 