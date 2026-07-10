#!/usr/bin/env python3
"""Linux deb 安装包构建脚本"""
import shutil, os, stat
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"
LINUX_DIR = PROJECT_ROOT / "linux"
BUILD_DIR = PROJECT_ROOT / "build_linux"

# 从 version.py 读取版本号
def get_version():
    vf = APP_DIR / "version.py"
    for line in vf.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("VERSION"):
            return line.split('"')[1]
    return "unknown"

# 需要复制的 Python 文件
PYTHON_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
]

def copy_source():
    """复制源码到构建目录"""
    app_target = BUILD_DIR / "usr" / "local" / "geometry-ai"
    app_target.mkdir(parents=True, exist_ok=True)

    # 复制 Python 文件
    for f in PYTHON_FILES:
        src = APP_DIR / f
        if src.exists():
            shutil.copy2(src, app_target / f)
            print(f"  + {f}")

    # 复制数据目录
    for d in ["articles", "templates"]:
        src = APP_DIR / d
        dst = app_target / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            # 排除 archive/ 子目录（历史备份文件，不需要打包）
            ignore_patterns = shutil.ignore_patterns("archive", "__pycache__", "*.pyc", ".DS_Store")
            shutil.copytree(src, dst, ignore=ignore_patterns)
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"  + {d}/ ({count} 文件, 已排除 archive/)")

    # 复制 requirements.txt
    req = APP_DIR / "requirements.txt"
    if req.exists():
        shutil.copy2(req, app_target / "requirements.txt")

    # 复制 .env.example
    env = APP_DIR / ".env.example"
    if env.exists():
        shutil.copy2(env, app_target / ".env.example")
    else:
        # 生成 .env.example
        (app_target / ".env.example").write_text(
            "# Geometry AI Server 配置\n"
            "# 必填: DeepSeek API Key (https://platform.deepseek.com/)\n"
            "GAI_API_KEY=在此\n"
            "# 可选配置\n"
            "GAI_BASE_URL=https://api.deepseek.com/v1\n"
            "GAI_MODEL=deepseek-chat\n"
            "GAI_MODEL_LITE=deepseek-chat\n"
            "GAI_MODEL_VISION=deepseek-chat\n"
            "GAI_EMBEDDING_MODEL=deepseek-chat\n"
            "# GAI_EMBEDDING_MODE=siliconflow  # default: SiliconFlow\n"
            "SILICONFLOW_API_KEY=\n"
            "EXTRA_MODELS=\n"
            "QUALITY_GATE_ENABLED=true\n",
            encoding="utf-8"
        )

    # 复制 uninstall.sh
    uninstall_src = LINUX_DIR / "uninstall_linux.sh"
    if uninstall_src.exists():
        shutil.copy2(uninstall_src, app_target / "uninstall.sh")

    print(f"  源码复制完成 -> {app_target}")

def generate_scripts():
    """生成安装脚本（修复路由为 /v1/vector/rebuild）"""
    build_root = BUILD_DIR / "usr" / "local" / "geometry-ai"

    # fix_index.sh
    fix_index = build_root / "fix_index.sh"
    fix_index.write_text(
        '#!/bin/bash\n'
        '# Geometry AI Server - 索引重建脚本\n'
        '# 不用 set -e，apt 等命令可能返回非零但实际成功\n'
        '\n'
        'if [ "$EUID" -ne 0 ]; then\n'
        '    echo "[!] 请使用 sudo 运行: sudo bash fix_index.sh"\n'
        '    exit 1\n'
        'fi\n'
        '\n'
        'APP_DIR="/usr/local/geometry-ai"\n'
        '\n'
        'echo "[1] 检查 API Key..."\n'
        'if grep -q \'GAI_API_KEY=在此\' "$APP_DIR/.env" 2>/dev/null; then\n'
        '    echo "[!] 错误: API Key 未配置！"\n'
        '    echo "    请先执行: sudo nano $APP_DIR/.env"\n'
        '    exit 1\n'
        'fi\n'
        'echo "  [ok] API Key 已配置"\n'
        '\n'
        'echo "[2] 检查文章文件..."\n'
        'COUNT=$(ls "$APP_DIR/articles"/*.md 2>/dev/null | wc -l)\n'
        'echo "  文章文件数: $COUNT"\n'
        'if [ "$COUNT" -eq 0 ]; then\n'
        '    echo "[!] 错误: 文章目录为空！"\n'
        '    exit 1\n'
        'fi\n'
        '\n'
        'echo "[3] 检查服务状态..."\n'
        'if ! systemctl is-active --quiet geometry-ai; then\n'
        '    echo "  服务未运行，重新启动..."\n'
        '    systemctl start geometry-ai\n'
        '    sleep 5\n'
        'fi\n'
        '\n'
        'echo "[4] 触发重建索引..."\n'
        'RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)\n'
        'echo "  响应: $RESP"\n'
        '\n'
        'if echo "$RESP" | grep -q \'\"success\": true\'; then\n'
        '    echo "  [ok] 索引重建成功！"\n'
        'else\n'
        '    echo "  [!] 索引重建失败，查看日志:"\n'
        '    echo "  sudo journalctl -u geometry-ai -n 50"\n'
        'fi\n',
        encoding="utf-8"
    )
    fix_index.chmod(fix_index.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    # install.sh
    version = get_version()
    install_sh = build_root / "install.sh"
    install_sh.write_text(
        '#!/bin/bash\n'
        '# Geometry AI Server - Ubuntu 安装脚本 v' + version + '\n'
        '# 不用 set -e，apt 等命令可能返回非零但实际成功\n'
        '\n'
        'if [ "$EUID" -ne 0 ]; then\n'
        '    echo "[!] 请使用 sudo 运行: sudo bash install.sh"\n'
        '    exit 1\n'
        'fi\n'
        '\n'
        'echo ""\n'
        'echo "  ========================================================="\n'
        'echo "      Geometry AI Server v' + version + ' - Ubuntu 安装"\n'
        'echo "  ========================================================="\n'
        'echo ""\n'
        '\n'
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"\n'
        'APP_DIR="/usr/local/geometry-ai"\n'
        '\n'
        'read -p "  输入 DeepSeek API Key (必填): " DEEPSEEK_KEY\n'
        'read -p "  输入 SiliconFlow API Key (可选,直接回车跳过): " SILICONFLOW_KEY\n'
        '# Step 1: Python 3.11+\n'
        'echo "[1/6] 检查 Python 环境（需要 3.11+）..."\n'
        'PYTHON=""\n'
        'MIN_VER=11\n'
        'for cmd in python3.13 python3.12 python3.11; do\n'
        '    if command -v "$cmd" &>/dev/null; then\n'
        '        ver=$($cmd -c "import sys; v=sys.version_info; print(str(v.major)+chr(46)+str(v.minor))" 2>/dev/null)\n'
        '        if [ "${ver%%.*}" = "3" ] && [ "${ver##*.}" -ge "$MIN_VER" ]; then\n'
        '            PYTHON="$cmd"\n'
        '            break\n'
        '        fi\n'
        '    fi\n'
        'done\n'
        'if [ -z "$PYTHON" ]; then\n'
        '    echo "  当前 Python 版本过低，尝试安装 Python 3.11..."\n'
        '    export DEBIAN_FRONTEND=noninteractive\n'
        '    apt-get update\n'
        '    apt-get install -y software-properties-common\n'
        '    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null\n'
        '    apt-get update\n'
        '    apt-get install -y python3.11 python3.11-pip python3.11-venv python3.11-dev\n'
        '    if ! command -v python3.11 &>/dev/null; then\n'
        '        echo "  PPA 安装失败，尝试从源码编译 Python 3.11..."\n'
        '        apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-compat-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev\n'
        '        cd /tmp\n'
        '        wget -q https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz\n'
        '        tar xzf Python-3.11.9.tgz\n'
        '        cd Python-3.11.9\n'
        '        ./configure --prefix=/usr/local --enable-optimizations --with-ensurepip=install > /dev/null 2>&1\n'
        '        make -j$(nproc) > /dev/null 2>&1\n'
        '        make altinstall > /dev/null 2>&1\n'
        '        cd /tmp\n'
        '        rm -rf Python-3.11.9 Python-3.11.9.tgz\n'
        '    fi\n'
        '    if command -v python3.11 &>/dev/null; then\n'
        '        PYTHON="python3.11"\n'
        '        echo "  [ok] Python 3.11 安装成功"\n'
        '    else\n'
        '        echo "[!] Python 3.11 安装失败"\n'
        '        echo "    请手动安装: https://docs.python.org/3/using/unix.html#building-python"\n'
        '        exit 1\n'
        '    fi\n'
        'fi\n'
        'PYTHON_PATH="$(command -v $PYTHON)"\n'
        'PY_VER=$($PYTHON -c "import sys; print(str(sys.version_info.major)+chr(46)+str(sys.version_info.minor))")\n'
        'echo "  Python: $PYTHON $PY_VER ($PYTHON_PATH)"\n'
        'if [ "${PY_VER##*.}" -lt "$MIN_VER" ]; then\n'
        '    echo "[!] 需要 Python 3.11+，当前 $PY_VER"\n'
        '    exit 1\n'
        'fi\n'
        '\n'
        '# Step 2: 复制文件\n'
        'echo "[2/6] 安装程序文件..."\n'
        'rm -rf "$APP_DIR" 2>/dev/null || true\n'
        'cp -r "$SCRIPT_DIR/app" "$APP_DIR"\n'
        'mkdir -p "$APP_DIR/chroma_db" "$APP_DIR/logs"\n'
        'chmod -R 755 "$APP_DIR"\n'
        '\n'
        '# 写入 .env（不修改模板文件 .env.example）\n'
        'cp "$APP_DIR/.env.example" "$APP_DIR/.env"\n'
        'if [ -n "$DEEPSEEK_KEY" ]; then\n'
        '    sed -i "s|GAI_API_KEY=在此|GAI_API_KEY=$DEEPSEEK_KEY|" "$APP_DIR/.env"\n'
        'fi\n'
        'if [ -n "$SILICONFLOW_KEY" ]; then\n'
        '    sed -i "s|SILICONFLOW_API_KEY=在此|SILICONFLOW_API_KEY=$SILICONFLOW_KEY|" "$APP_DIR/.env"\n'
        'fi\n'
        'echo "  [ok] 文件已安装到 $APP_DIR"\n'
        '\n'
        '# Step 3: pip 依赖\n'
        'echo "[3/6] 安装 Python 依赖..."\n'
        'MIRRORS="https://mirrors.aliyun.com/pypi/simple/ https://pypi.tuna.tsinghua.edu.cn/simple/"\n'
        'PIP_OK=0\n'
        'for mirror in $MIRRORS; do\n'
        '    if $PYTHON -m pip install -i $mirror -r "$APP_DIR/requirements.txt" -q 2>/dev/null; then\n'
        '        PIP_OK=1\n'
        '        break\n'
        '    fi\n'
        'done\n'
        'if [ "$PIP_OK" -eq 0 ]; then\n'
        '    echo "[!] pip 依赖安装失败，尝试默认源..."\n'
        '    if ! $PYTHON -m pip install -r "$APP_DIR/requirements.txt" -q; then\n'
        '        echo "[!] 所有镜像源均失败，请手动安装:"\n'
        '        echo "    $PYTHON -m pip install -r $APP_DIR/requirements.txt"\n'
        '        exit 1\n'
        '    fi\n'
        'fi\n'
        'echo "  [ok] 依赖安装完成"\n'
        '\n'
        '# Step 4: systemd 服务\n'
        'echo "[4/6] 注册 systemd 服务..."\n'
        '# 创建非特权用户运行服务\n'
        'if ! id -u geometry-ai &>/dev/null; then\n'
        '    useradd -r -s /usr/sbin/nologin -d "$APP_DIR" geometry-ai\n'
        'fi\n'
        'chown -R geometry-ai:geometry-ai "$APP_DIR"\n'
        'cat > /etc/systemd/system/geometry-ai.service << SERVICEEOF\n'
        '[Unit]\n'
        'Description=Geometry AI Server\n'
        'After=network.target\n'
        '\n'
        '[Service]\n'
        'Type=simple\n'
        'User=geometry-ai\n'
        'Group=geometry-ai\n'
        'WorkingDirectory=$APP_DIR\n'
        'ExecStart=$PYTHON_PATH $APP_DIR/server.py\n'
        'Restart=always\n'
        'RestartSec=5\n'
        'StandardOutput=journal\n'
        'StandardError=journal\n'
        'Environment=PYTHONUNBUFFERED=1\n'
        '\n'
        '[Install]\n'
        'WantedBy=multi-user.target\n'
        'SERVICEEOF\n'
        'systemctl daemon-reload\n'
        'systemctl enable geometry-ai\n'
        'systemctl start geometry-ai\n'
        '\n'
        'echo "  等待服务启动..."\n'
        'for i in $(seq 1 15); do\n'
        '    if curl -s http://localhost:5000/health >/dev/null 2>&1; then\n'
        '        echo "  [ok] 服务已启动 (端口 5000)"\n'
        '        break\n'
        '    fi\n'
        '    sleep 2\n'
        'done\n'
        '\n'
        '# Step 5: 安装 Open WebUI\n'
        'echo "[5/7] 安装 Open WebUI..."\n'
        'SYS_PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")\n'
        'WEBUI_VENV="$APP_DIR/open-webui-venv"\n'
        'WEBUI_BIN=""\n'
        'if [ "$SYS_PY_MINOR" -ge 13 ]; then\n'
        '    echo "  系统 Python 3.$SYS_PY_MINOR >= 3.13，创建 Python 3.12 虚拟环境..."\n'
        '    apt-get install -y python3.12 python3.12-venv 2>/dev/null\n'
        '    python3.12 -m venv "$WEBUI_VENV"\n'
        '    "$WEBUI_VENV/bin/pip" install --upgrade pip -q\n'
        '    echo "  安装 PyTorch CPU 版（跳过 CUDA，节省空间）..."\n'
        '    "$WEBUI_VENV/bin/pip" install torch --index-url https://download.pytorch.org/whl/cpu\n'
        '    echo "  安装 Open WebUI..."\n'
        '    "$WEBUI_VENV/bin/pip" install open-webui\n'
        '    WEBUI_BIN="$WEBUI_VENV/bin/open-webui"\n'
        'else\n'
        '    if command -v open-webui &>/dev/null; then\n'
        '        WEBUI_BIN="open-webui"\n'
        '    elif $PYTHON -m pip show open-webui &>/dev/null; then\n'
        '        WEBUI_BIN="$PYTHON -m open_webui"\n'
        '    fi\n'
        '    if [ -z "$WEBUI_BIN" ]; then\n'
        '        echo "  安装 PyTorch CPU 版..."\n'
        '        $PYTHON -m pip install --break-system-packages --ignore-installed torch --index-url https://download.pytorch.org/whl/cpu\n'
        '        echo "  安装 Open WebUI（可能需要几分钟）..."\n'
        '        $PYTHON -m pip install --break-system-packages --ignore-installed open-webui\n'
        '        WEBUI_BIN="open-webui"\n'
        '    fi\n'
        'fi\n'
        'if [ -n "$WEBUI_BIN" ]; then\n'
        '    echo "  [ok] Open WebUI 已安装"\n'
        'else\n'
        '    echo "  [!] Open WebUI 安装失败"\n'
        'fi\n'
        '\n'
        '# Step 5.5: 注册 Open WebUI systemd 服务\n'
        'echo "[6/7] 注册 Open WebUI 服务..."\n'
        'if [ -n "$WEBUI_BIN" ] && [ "$WEBUI_BIN" != "" ]; then\n'
        '    # 生成随机密钥\n'
        '    WEBUI_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32 2>/dev/null || echo "fallback-$(date +%s)-$$")\n'
        '    cat > /etc/systemd/system/open-webui.service << WEBUIEOF\n'
        '[Unit]\n'
        'Description=Open WebUI\n'
        'After=network.target\n'
        '\n'
        '[Service]\n'
        'Type=simple\n'
        'User=geometry-ai\n'
        'Group=geometry-ai\n'
        'WorkingDirectory=$APP_DIR\n'
        'ExecStart=$WEBUI_BIN serve --port 8080\n'
        'Restart=always\n'
        'RestartSec=5\n'
        'StandardOutput=journal\n'
        'StandardError=journal\n'
        'Environment=PYTHONUNBUFFERED=1\n'
        'Environment=OPENAI_API_BASE_URLS=http://localhost:5000/v1\n'
        'Environment=OPENAI_API_KEYS=${DEEPSEEK_KEY}\n'
        'Environment=WEBUI_NAME=Geometry AI\n'
        'Environment=WEBUI_SECRET_KEY=${WEBUI_SECRET}\n'
        '\n'
        '[Install]\n'
        'WantedBy=multi-user.target\n'
        'WEBUIEOF\n'
        '    systemctl daemon-reload\n'
        '    systemctl enable open-webui\n'
        '    systemctl start open-webui\n'
        '    echo "  等待 Open WebUI 启动..."\n'
        '    for i in $(seq 1 15); do\n'
        '        if curl -s http://localhost:8080 >/dev/null 2>&1; then\n'
        '            echo "  [ok] Open WebUI 已启动 (端口 8080)"\n'
        '            break\n'
        '        fi\n'
        '        sleep 2\n'
        '    done\n'
        'else\n'
        '    echo "  [!] 跳过 Open WebUI 服务注册"\n'
        'fi\n'
        '\n'
        '# Step 6: 重建索引\n'
        'echo "[7/7] 重建知识库索引..."\n'
        'ARTICLE_COUNT=$(find "$APP_DIR/articles" -maxdepth 1 -name \'*.md\' | wc -l)\n'
        'echo "  文章文件数: $ARTICLE_COUNT"\n'
        'if [ "$ARTICLE_COUNT" -gt 0 ]; then\n'
        '    RESP=$(curl -s -X POST http://localhost:5000/v1/vector/rebuild)\n'
        '    if echo "$RESP" | grep -q \'\"success\": true\'; then\n'
        '        echo "  [ok] 知识库索引已重建"\n'
        '    else\n'
        '        echo "  [!] 索引重建请求已发送（可能需要几分钟）"\n'
        '        echo "  响应: $RESP"\n'
        '        echo "  手动重建: sudo bash $APP_DIR/fix_index.sh"\n'
        '    fi\n'
        'fi\n'
        '\n'
        'echo ""\n'
        'echo "  ========================================================="\n'
        'echo "  [ok] 安装完成！"\n'
        'echo "  ========================================================="\n'
        'echo ""\n'
        'echo "  管理页面: http://localhost:5000/admin"\n'
        'echo "  健康检查: http://localhost:5000/health"\n'
        'echo "  配置文件: $APP_DIR/.env"\n'
        'echo ""\n'
        'echo "  状态: sudo systemctl status geometry-ai"\n'
        'echo "  日志: sudo journalctl -u geometry-ai -f"\n'
        'echo "  卸载: sudo bash $APP_DIR/uninstall.sh"\n'
        '',
        encoding="utf-8"
    )
    install_sh.chmod(install_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    # uninstall.sh
    uninstall_sh = build_root / "uninstall.sh"
    uninstall_sh.write_text(
        '#!/bin/bash\n'
        '# Geometry AI Server - Ubuntu 卸载脚本 v' + version + '\n'
        '# 不用 set -e，apt 等命令可能返回非零但实际成功\n'
        '\n'
        'APP_DIR="/usr/local/geometry-ai"\n'
        '\n'
        'echo ""\n'
        'echo "  ========================================================="\n'
        'echo "      Geometry AI Server v' + version + ' - 卸载"\n'
        'echo "  ========================================================="\n'
        'echo ""\n'
        '\n'
        'if [ "$EUID" -ne 0 ]; then\n'
        '    echo "[!] 请使用 sudo 运行: sudo bash uninstall.sh"\n'
        '    exit 1\n'
        'fi\n'
        '\n'
        'echo "[1/4] 停止服务..."\n'
        'systemctl stop geometry-ai 2>/dev/null || true\n'
        'systemctl disable geometry-ai 2>/dev/null || true\n'
        'echo "  [ok] 服务已停止"\n'
        '\n'
        'echo "[2/4] 删除 systemd 服务文件..."\n'
        'rm -f /etc/systemd/system/geometry-ai.service\n'
        'systemctl daemon-reload\n'
        'echo "  [ok] systemd 已清理"\n'
        '\n'
        'echo "[3/4] 卸载 pip 依赖..."\n'
        'if [ -f "$APP_DIR/requirements.txt" ]; then\n'
        '    echo "  以下依赖将被卸载:"\n'
        '    cat "$APP_DIR/requirements.txt"\n'
        '    read -p "  确认卸载这些 pip 包？(y/N): " CONFIRM_PIP\n'
        '    if [ "$CONFIRM_PIP" = "y" ] || [ "$CONFIRM_PIP" = "Y" ]; then\n'
        '        pip3 uninstall -y -r "$APP_DIR/requirements.txt" 2>/dev/null || true\n'
        '        echo "  [ok] pip 依赖已卸载"\n'
        '    else\n'
        '        echo "  跳过 pip 依赖卸载"\n'
        '    fi\n'
        'else\n'
        '    echo "  跳过（未找到 requirements.txt）"\n'
        'fi\n'
        '\n'
        'read -p "是否删除向量数据库和日志？(y/N): " CONFIRM_DATA\n'
        'if [ "$CONFIRM_DATA" = "y" ] || [ "$CONFIRM_DATA" = "Y" ]; then\n'
        '    rm -rf "$APP_DIR/chroma_db" 2>/dev/null || true\n'
        '    rm -rf "$APP_DIR/logs" 2>/dev/null || true\n'
        '    rm -rf "$APP_DIR/models_cache" 2>/dev/null || true\n'
        '    echo "  [ok] 运行时数据已删除"\n'
        'else\n'
        '    echo "  保留运行时数据"\n'
        'fi\n'
        '\n'
        'read -p "是否删除整个安装目录 $APP_DIR？(y/N): " CONFIRM_DIR\n'
        'if [ "$CONFIRM_DIR" = "y" ] || [ "$CONFIRM_DIR" = "Y" ]; then\n'
        '    rm -rf "$APP_DIR"\n'
        '    echo "  [ok] 安装目录已删除"\n'
        'else\n'
        '    echo "  保留安装目录"\n'
        'fi\n'
        '\n'
        'echo ""\n'
        'echo "  ========================================================="\n'
        'echo "  [ok] 卸载完成！"\n'
        'echo "  ========================================================="\n'
        'echo ""\n',
        encoding="utf-8"
    )
    uninstall_sh.chmod(uninstall_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    print("  + install.sh (路由已修复为 /v1/vector/rebuild)")
    print("  + fix_index.sh (路由已修复为 /v1/vector/rebuild)")
    print("  + uninstall.sh")

def create_deb():
    """创建 DEBIAN 控制文件"""
    deb_dir = BUILD_DIR / "DEBIAN"
    deb_dir.mkdir(exist_ok=True)
    version = get_version()

    (deb_dir / "control").write_text(
        f"Package: geometry-ai-server\n"
        f"Version: {version}\n"
        f"Section: science\n"
        f"Priority: optional\n"
        f"Architecture: amd64\n"
        f"Depends: python3 (>= 3.11), python3-pip, systemd\n"
        f"Recommends: sqlite3, curl\n"
        f"Maintainer: Geometry AI <support@geometry-ai.org>\n"
        f"Description: Geometry AI Server - Geometric Theory AI\n"
        f" Based on Geometric Theory framework.\n"
        f" Features: vector search, multi-turn tools, knowledge base.\n",
        encoding="utf-8"
    )

    (deb_dir / "postinst").write_text(
        '#!/bin/bash\n'
        'set -e\n'
        'APP_DIR="/usr/local/geometry-ai"\n'
        'if [ ! -f "$APP_DIR/.env" ]; then\n'
        '    cp "$APP_DIR/.env.example" "$APP_DIR/.env" 2>/dev/null || true\n'
        'fi\n'
        'mkdir -p "$APP_DIR/chroma_db" "$APP_DIR/logs"\n'
        'chmod 755 "$APP_DIR/chroma_db" "$APP_DIR/logs"\n'
        'echo "Geometry AI Server 已安装，请运行: sudo bash /usr/local/geometry-ai/install.sh"\n',
        encoding="utf-8"
    )
    (deb_dir / "postinst").chmod(0o755)

    (deb_dir / "prerm").write_text(
        '#!/bin/bash\n'
        'systemctl stop geometry-ai 2>/dev/null || true\n'
        'systemctl disable geometry-ai 2>/dev/null || true\n',
        encoding="utf-8"
    )
    (deb_dir / "prerm").chmod(0o755)

    print(f"  + DEBIAN/control (版本 {version})")

def create_zip():
    """打包为 zip（扁平结构，install.sh 在根目录）"""
    version = get_version()
    zip_name = f"geometry-ai-server_ubuntu_v{version}_amd64.zip"
    zip_path = PROJECT_ROOT / zip_name
    prefix = f"geometry-ai-server_{version}_amd64"

    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        app_build = BUILD_DIR / "usr" / "local" / "geometry-ai"

        # install.sh、fix_index.sh 放在根目录
        for script in ["install.sh", "fix_index.sh", "uninstall.sh"]:
            sp = app_build / script
            if sp.exists():
                zf.write(sp, f"{prefix}/{script}")
                print(f"  + {script} (根目录)")

        # DEBIAN/ 放在根目录（供 dpkg-deb 构建用）
        deb_dir = BUILD_DIR / "DEBIAN"
        if deb_dir.exists():
            for f in sorted(deb_dir.rglob("*")):
                if f.is_file():
                    zf.write(f, f"{prefix}/DEBIAN/{f.name}")

        # 程序文件放在 app/ 子目录
        for file in sorted(app_build.rglob("*")):
            if file.is_file():
                if "__pycache__" in str(file) or file.suffix == ".pyc":
                    continue
                if file.name == ".DS_Store":
                    continue
                rel = file.relative_to(app_build)
                zf.write(file, f"{prefix}/app/{rel}")

    size = zip_path.stat().st_size
    print(f"\n  打包完成: {zip_name} ({size/1024/1024:.1f} MB)")
    print(f"  安装方式: unzip {zip_name} && sudo bash {prefix}/install.sh")

def build():
    print(f"=== Geometry AI Linux 构建器 v{get_version()} ===\n")

    # 清理
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    print("[1/4] 复制源码...")
    copy_source()

    print("\n[2/4] 生成安装脚本...")
    generate_scripts()

    print("\n[3/4] 创建 DEBIAN 控制文件...")
    create_deb()

    print("\n[4/4] 打包 zip...")
    create_zip()

    print("\n=== 构建完成 ===")

if __name__ == "__main__":
    build()
