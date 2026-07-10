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
        "install.sh": INSTALL_SH_TEMPLATE,
        "upgrade.sh": UPGRADE_SH_TEMPLATE,
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
    zip_name = f"geometry-ai-server_linux_v{version}.zip"
    zip_path = PROJECT_ROOT / zip_name
    prefix = f"geometry-ai-server_{version}"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for script in ["install.sh", "upgrade.sh", "uninstall.sh", "fix-index.sh"]:
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
    print(f"  安装: unzip {zip_name} && cd {prefix} && sudo bash install.sh")


# ─── Template: install.sh ─────────────────────────────────────
INSTALL_SH_TEMPLATE = """#!/bin/bash
# Geometry AI Server v{VERSION} - Linux 全自动安装
set -euo pipefail

RED='\\033[0;31m'; GREEN='\\033[0;32m'; CYAN='\\033[0;36m'; NC='\\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${CYAN}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "  Geometry AI Server v{VERSION} - Linux 全自动安装"
echo "  ================================================"
echo ""

if [ "$EUID" -ne 0 ]; then error "请使用 sudo 运行"; exit 1; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="/usr/local/geometry-ai"
SERVICE_USER="geometry-ai"

# ── 1. Python 3.11+ ──
warn "[1/7] 检查 Python 环境（需要 3.11+）..."
PYTHON=""
for cmd in python3.13 python3.12 python3.11; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        major=${ver%%.*}; minor=${ver##*.}
        if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then PYTHON="$cmd"; break; fi
    fi
done

if [ -z "$PYTHON" ]; then
    warn "Python 3.11+ 未安装，正在自动安装..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq && apt-get install -y -qq software-properties-common 2>/dev/null || true
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null && apt-get update -qq || true
    apt-get install -y -qq python3.11 python3.11-pip python3.11-venv python3.11-dev 2>/dev/null || {
        warn "PPA 失败，从源码编译 Python 3.11..."
        apt-get install -y -qq build-essential zlib1g-dev libncurses5-dev libgdbm-compat-dev \\
            libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
        cd /tmp
        wget -q https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
        tar xzf Python-3.11.9.tgz && cd Python-3.11.9
        ./configure --prefix=/usr/local --enable-optimizations --with-ensurepip=install >/dev/null 2>&1
        make -j$(nproc) >/dev/null 2>&1 && make altinstall >/dev/null 2>&1
        cd /tmp && rm -rf Python-3.11.9 Python-3.11.9.tgz
    }
    PYTHON="python3.11"
fi

command -v "$PYTHON" >/dev/null || { error "Python 安装失败"; exit 1; }
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PY_VER ($(command -v $PYTHON))"

# ── 2. 安装文件 ──
warn "[2/7] 安装程序文件..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR" "$APP_DIR/chroma_db" "$APP_DIR/logs"
cp -r "$SCRIPT_DIR/app"/* "$APP_DIR/"
info "文件已安装到 $APP_DIR"

# ── 3. 虚拟环境 + 依赖 ──
warn "[3/7] 创建虚拟环境并安装依赖..."
$PYTHON -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip -q

MIRRORS=("https://pypi.tuna.tsinghua.edu.cn/simple" "https://mirrors.aliyun.com/pypi/simple/" "https://pypi.org/simple")
INSTALLED=0
for m in "${MIRRORS[@]}"; do
    if pip install -i "$m" -r "$APP_DIR/requirements.txt" -q 2>/dev/null; then
        INSTALLED=1; break
    fi
done
if [ "$INSTALLED" -eq 0 ]; then
    pip install -r "$APP_DIR/requirements.txt" -q || {
        error "依赖安装失败，手动执行: pip install -r $APP_DIR/requirements.txt"
        exit 1
    }
fi
info "依赖安装完成"

# ── 4. 配置 API Key ──
warn "[4/7] 配置 API Key..."
if [ -f "$APP_DIR/.env" ] && ! grep -q "GAI_API_KEY=在此" "$APP_DIR/.env" 2>/dev/null; then
    info "已有配置，跳过"
else
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    read -p "  输入 DeepSeek API Key (必填): " DEEPSEEK_KEY
    read -p "  输入 SiliconFlow API Key (可选): " SILICONFLOW_KEY
    sed -i "s|GAI_API_KEY=在此|GAI_API_KEY=$DEEPSEEK_KEY|" "$APP_DIR/.env"
    [ -n "$SILICONFLOW_KEY" ] && sed -i "s|SILICONFLOW_API_KEY=|SILICONFLOW_API_KEY=$SILICONFLOW_KEY|" "$APP_DIR/.env"
    info "配置已保存"
fi

# ── 5. 防火墙 ──
warn "[5/7] 配置防火墙..."
if command -v ufw &>/dev/null; then
    ufw allow 5000/tcp comment 'Geometry AI Server' >/dev/null 2>&1 || true
    ufw allow 8080/tcp comment 'Geometry AI WebUI' >/dev/null 2>&1 || true
    info "UFW 规则已添加"
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-port=5000/tcp >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-port=8080/tcp >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
    info "firewalld 规则已添加"
else
    warn "未检测到防火墙工具，跳过"
fi

# ── 6. systemd 服务 ──
warn "[6/7] 注册 systemd 服务..."
id -u "$SERVICE_USER" &>/dev/null || useradd -r -s /usr/sbin/nologin -d "$APP_DIR" "$SERVICE_USER"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

cat > /etc/systemd/system/geometry-ai.service << EOFSVC
[Unit]
Description=Geometry AI Server
After=network.target
[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOFSVC

systemctl daemon-reload
systemctl enable geometry-ai
systemctl start geometry-ai
info "systemd 服务已注册"

warn "  等待服务启动..."
for i in $(seq 1 15); do
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        info "Geometry AI Server 已启动 (端口 5000)"
        break
    fi
    sleep 2
done

# ── 7. Open WebUI ──
warn "[7/7] 安装 Open WebUI..."
if $PYTHON -c "import open_webui" 2>/dev/null; then
    info "Open WebUI 已安装"
else
    $PYTHON -m pip install --disable-pip-version-check -i https://pypi.tuna.tsinghua.edu.cn/simple open-webui -q 2>/dev/null || \
    $PYTHON -m pip install open-webui -q 2>/dev/null || true
fi

if $PYTHON -c "import open_webui" 2>/dev/null; then
    WEBUI_SECRET=$($PYTHON -c "import secrets; print(secrets.token_hex(32))")
    cat > /etc/systemd/system/geometry-ai-webui.service << EOFSVC
[Unit]
Description=Geometry AI WebUI (Open WebUI)
After=network.target geometry-ai.service
[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
ExecStart=$APP_DIR/venv/bin/python -m open_webui serve
Restart=always
RestartSec=5
Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1
Environment=OPENAI_API_KEYS=not-needed
Environment=WEBUI_SECRET_KEY=$WEBUI_SECRET
Environment=WEBUI_NAME=Geometry AI
Environment=WEBUI_PORT=8080
[Install]
WantedBy=multi-user.target
EOFSVC
    systemctl daemon-reload
    systemctl enable geometry-ai-webui
    systemctl start geometry-ai-webui
    info "Open WebUI 已启动 (端口 8080)"
else
    warn "Open WebUI 安装跳过，可手动: pip install open-webui"
fi

# ── 完成 ──
echo ""
echo "  ================================================"
echo "  [OK] 安装完成！"
echo "  ================================================"
echo ""
echo "  管理面板: http://localhost:5000/admin"
echo "  聊天界面: http://localhost:8080"
echo "  配置文件: $APP_DIR/.env"
echo ""
echo "  状态: sudo systemctl status geometry-ai"
echo "  日志: sudo journalctl -u geometry-ai -f"
echo "  升级: sudo bash $APP_DIR/../upgrade.sh"
echo "  卸载: sudo bash $SCRIPT_DIR/uninstall.sh"
echo ""
"""

# ─── Template: upgrade.sh ─────────────────────────────────────
UPGRADE_SH_TEMPLATE = """#!/bin/bash
# Geometry AI Server v{VERSION} - 升级脚本（保留配置和数据）
set -euo pipefail

RED='\\033[0;31m'; GREEN='\\033[0;32m'; CYAN='\\033[0;36m'; NC='\\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${CYAN}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "  Geometry AI Server v{VERSION} - 升级"
echo "  ================================================"
echo ""

if [ "$EUID" -ne 0 ]; then exec sudo bash "$0" "$@"; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="/usr/local/geometry-ai"
SERVICE_USER="geometry-ai"

# ── 1. 检查旧版 ──
warn "[1/5] 检查现有安装..."
if [ ! -d "$APP_DIR" ]; then
    error "未找到旧版安装 ($APP_DIR)，请先运行 install.sh"
    exit 1
fi
if [ ! -d "$APP_DIR/venv" ]; then
    error "未找到虚拟环境 ($APP_DIR/venv)，请先运行 install.sh"
    exit 1
fi
info "发现旧版安装: $APP_DIR"

# ── 2. 备份 + 停止 ──
warn "[2/5] 备份配置并停止服务..."
[ -f "$APP_DIR/.env" ] && cp "$APP_DIR/.env" "$APP_DIR/.env.upgrade-bak"
systemctl stop geometry-ai-webui 2>/dev/null || true
systemctl stop geometry-ai 2>/dev/null || true
sleep 2
info "已停止旧服务，.env 已备份为 .env.upgrade-bak"

# ── 3. 更新源码 ──
warn "[3/5] 更新源码文件..."
# 保留: venv/ .env chroma_db/ logs/ conversations.db
for item in "$APP_DIR"/*; do
    name=$(basename "$item")
    case "$name" in
        venv|.env|chroma_db|logs|conversations.db|.env.upgrade-bak)
            ;;
        *)
            rm -rf "$item"
            ;;
    esac
done

cp -r "$SCRIPT_DIR/app"/* "$APP_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
info "源码已更新"

# ── 4. 更新依赖 ──
warn "[4/5] 更新 Python 依赖..."
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip -q
MIRRORS=("https://pypi.tuna.tsinghua.edu.cn/simple" "https://mirrors.aliyun.com/pypi/simple/" "https://pypi.org/simple")
for m in "${MIRRORS[@]}"; do
    if pip install -i "$m" -r "$APP_DIR/requirements.txt" -q 2>/dev/null; then
        break
    fi
done
info "依赖已更新"

# ── 5. 重启服务 ──
warn "[5/5] 重启服务..."
systemctl daemon-reload
systemctl start geometry-ai
sleep 5
if curl -s http://localhost:5000/health >/dev/null 2>&1; then
    info "Geometry AI Server 已启动"
    systemctl start geometry-ai-webui 2>/dev/null || true
    info "升级完成！"
else
    warn "服务启动中，请稍后检查: sudo journalctl -u geometry-ai -f"
fi
echo ""
echo "  保留的配置:"
echo "    .env         → 你的 API Key 和设置（已额外备份为 .env.upgrade-bak）"
echo "    venv/        → Python 虚拟环境"
echo "    chroma_db/   → 向量数据库"
echo "    logs/        → 历史日志"
echo "    conversations.db → 对话记录"
echo ""
echo "  回滚:"
echo "    sudo systemctl stop geometry-ai"
echo "    cp $APP_DIR/.env.upgrade-bak $APP_DIR/.env"
echo "    重新运行旧版 install.sh"
echo ""
"""

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
    echo "[!] 未找到配置文件，请先运行 install.sh"
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
