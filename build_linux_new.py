#!/usr/bin/env python3
"""Geometry AI Server - Linux 全自动安装包构建脚本（全新）"""
import shutil, os, stat, zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"
BUILD_DIR = PROJECT_ROOT / "build_linux_new"

PYTHON_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
    "master_client.py",
]
DATA_DIRS = ["articles", "templates"]
IGNORE_DIRS = {"__pycache__", "archive", ".obsidian", "copilot", "node_modules", ".git"}


def get_version():
    vf = APP_DIR / "version.py"
    for line in vf.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("VERSION"):
            return line.split('"')[1]
    return "unknown"


def copy_source():
    app_target = BUILD_DIR / "app"
    app_target.mkdir(parents=True, exist_ok=True)

    for f in PYTHON_FILES:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)
            print(f"  + {f}")

    for d in DATA_DIRS:
        src = APP_DIR / d
        dst = app_target / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=lambda d, c: {
                x for x in c if x in IGNORE_DIRS or x == ".DS_Store"
            })
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"  + {d}/ ({count} files)")

    for f in ["requirements.txt", ".env.example"]:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)

    print(f"  Source -> {app_target}")


def generate_scripts():
    version = get_version()

    scripts = {
        "setup.sh": SETUP_SH_TEMPLATE,
        "uninstall.sh": UNINSTALL_SH_TEMPLATE,
        "fix-index.sh": FIX_INDEX_SH_TEMPLATE,
    }
    for name, content in scripts.items():
        text = content.replace("{VERSION}", version)
        path = BUILD_DIR / name
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IRWXU | stat.S_IRWXG)
        print(f"  + {name}")


def build():
    global version
    version = get_version()
    print(f"=== Geometry AI Linux 安装包构建 v{version} ===\n")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    print("[1/3] 复制源码...")
    copy_source()

    print("\n[2/3] 生成安装脚本...")
    generate_scripts()

    print("\n[3/3] 打包 zip...")
    folder_name = f"geometry-ai-server"
    zip_name = f"{folder_name}_linux_v{version}.zip"
    zip_path = PROJECT_ROOT / zip_name
    prefix = folder_name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for script in ["setup.sh", "uninstall.sh", "fix-index.sh"]:
            sp = BUILD_DIR / script
            if sp.exists():
                zf.write(sp, f"{prefix}/{script}")

        app_build = BUILD_DIR / "app"
        for file in sorted(app_build.rglob("*")):
            if file.is_file():
                if "__pycache__" in str(file) or file.suffix == ".pyc":
                    continue
                if file.name == ".DS_Store":
                    continue
                rel = file.relative_to(app_build)
                zf.write(file, f"{prefix}/app/{rel}")

    size = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n  打包完成: {zip_name} ({size:.1f} MB)")
    print(f"  安装: unzip {zip_name} && cd {prefix} && sudo bash setup.sh")


# ─── Template: setup.sh（智能安装/升级）─────────────────────
SETUP_SH_TEMPLATE = """#!/bin/bash
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
RED='\\033[0;31m'; GREEN='\\033[0;32m'; YELLOW='\\033[1;33m'; BLUE='\\033[0;34m'; NC='\\033[0m'
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
        PIP_MIRROR=""
        for m in "https://mirrors.aliyun.com/pypi/simple/" "https://pypi.tuna.tsinghua.edu.cn/simple" "https://pypi.org/simple"; do
            if curl -s --max-time 3 "$m" >/dev/null 2>&1; then PIP_MIRROR="-i $m"; break; fi
        done
        "$INSTALL_DIR/venv/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | tail -3 || true
        "$INSTALL_DIR/venv/bin/pip" install $PIP_MIRROR open-webui -q 2>&1 | tail -3 || true
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
    PIP_MIRROR=""
    for m in "https://mirrors.aliyun.com/pypi/simple/" "https://pypi.tuna.tsinghua.edu.cn/simple" "https://pypi.org/simple"; do
        if curl -s --max-time 3 "$m" >/dev/null 2>&1; then PIP_MIRROR="-i $m"; break; fi
    done
    if ! "$INSTALL_DIR/venv/bin/python3" -c "import open_webui" 2>/dev/null; then
        "$INSTALL_DIR/venv/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | tail -3 || true
        "$INSTALL_DIR/venv/bin/pip" install $PIP_MIRROR open-webui -q 2>&1 | tail -3 || true
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
echo """


# ─── Template: uninstall.sh ───────────────────────────────────
UNINSTALL_SH_TEMPLATE = """#!/bin/bash
# Geometry AI Server - 卸载脚本
set -euo pipefail

RED='\\033[0;31m'; GREEN='\\033[0;32m'; NC='\\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${CYAN}[→]${NC} $1"; }

APP_DIR="/usr/local/geometry-ai"

echo ""
echo "  Geometry AI Server - 卸载"
echo "  ================================================"
echo ""

if [ "$EUID" -ne 0 ]; then echo "请使用 sudo 运行"; exit 1; fi

warn "停止并删除服务..."
systemctl stop geometry-ai-webui 2>/dev/null || true
systemctl stop geometry-ai 2>/dev/null || true
systemctl disable geometry-ai-webui 2>/dev/null || true
systemctl disable geometry-ai 2>/dev/null || true
rm -f /etc/systemd/system/geometry-ai.service
rm -f /etc/systemd/system/geometry-ai-webui.service
systemctl daemon-reload
info "服务已删除"

warn "删除防火墙规则..."
if command -v ufw &>/dev/null; then
    ufw delete allow 5000/tcp >/dev/null 2>&1 || true
    ufw delete allow 8080/tcp >/dev/null 2>&1 || true
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --remove-port=5000/tcp >/dev/null 2>&1 || true
    firewall-cmd --permanent --remove-port=8080/tcp >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
fi
info "防火墙规则已删除"

if id -u geometry-ai &>/dev/null; then
    userdel geometry-ai 2>/dev/null || true
    info "系统用户已删除"
fi

read -p "删除运行时数据 (chroma_db, logs)? (y/N): " ans1
if [ "$ans1" = "y" ] || [ "$ans1" = "Y" ]; then
    rm -rf "$APP_DIR/chroma_db" "$APP_DIR/logs" "$APP_DIR/venv"
    info "运行时数据已删除"
fi

read -p "删除整个安装目录? (y/N): " ans2
if [ "$ans2" = "y" ] || [ "$ans2" = "Y" ]; then
    rm -rf "$APP_DIR"
    info "安装目录已删除"
fi

echo ""
info "卸载完成"
"""

# ─── Template: fix-index.sh ───────────────────────────────────
FIX_INDEX_SH_TEMPLATE = """#!/bin/bash
# Geometry AI Server - 知识库索引重建
APP_DIR="/usr/local/geometry-ai"
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[!] 未找到配置文件，请先运行 setup.sh"
    exit 1
fi
if ! systemctl is-active --quiet geometry-ai; then
    echo "[!] 服务未运行"
    exit 1
fi
echo "正在重建知识库索引..."
RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)
if echo "$RESP" | grep -q '"success": true'; then
    echo "[✓] 索引重建成功"
else
    echo "[!] 索引重建请求已发送，检查日志: journalctl -u geometry-ai -n 20"
fi
"""


if __name__ == "__main__":
    build()
