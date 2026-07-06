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
            shutil.copytree(src, dst)
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"  + {d}/ ({count} 文件)")

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
        'set -e\n'
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
        'set -e\n'
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
        '\n'
        '# Step 1: Python\n'
        'echo "[1/5] 检查 Python 环境..."\n'
        'PYTHON=""\n'
        'for cmd in python3.13 python3.12 python3.11 python3.10 python3; do\n'
        '    if command -v "$cmd" &>/dev/null; then\n'
        '        ver=$($cmd -c "import sys; print(sys.version_info.major .sys.version_info.minor)" 2>/dev/null)\n'
        '        if [ "${ver%%.*}" = "3" ] && [ "${ver##*.}" -ge 10 ] 2>/dev/null; then\n'
        '            PYTHON="$cmd"\n'
        '            break\n'
        '        fi\n'
        '    fi\n'
        'done\n'
        'if [ -z "$PYTHON" ]; then\n'
        '    export DEBIAN_FRONTEND=noninteractive\n'
        '    apt-get update -qq 2>/dev/null\n'
        '    apt-get install -y python3 python3-pip 2>/dev/null || true\n'
        '    PYTHON="python3"\n'
        'fi\n'
        'PYTHON_PATH="$(command -v $PYTHON)"\n'
        'echo "  Python: $PYTHON ($($PYTHON --version 2>&1))"\n'
        '\n'
        '# Step 2: 复制文件\n'
        'echo "[2/5] 安装程序文件..."\n'
        'rm -rf "$APP_DIR" 2>/dev/null || true\n'
        'cp -r "$SCRIPT_DIR/usr/local/geometry-ai" "/usr/local/"\n'
        'mkdir -p "$APP_DIR/chroma_db" "$APP_DIR/logs"\n'
        'chmod -R 755 "$APP_DIR"\n'
        '\n'
        '# 写入 .env\n'
        'if [ -n "$DEEPSEEK_KEY" ]; then\n'
        '    sed -i "s|GAI_API_KEY=在此|GAI_API_KEY=$DEEPSEEK_KEY|" "$APP_DIR/.env.example"\n'
        'fi\n'
        'if [ -n "$SILICONFLOW_KEY" ]; then\n'
        '    sed -i "s|SILICONFLOW_API_KEY=|SILICONFLOW_API_KEY=$SILICONFLOW_KEY|" "$APP_DIR/.env.example"\n'
        'fi\n'
        'cp "$APP_DIR/.env.example" "$APP_DIR/.env"\n'
        'echo "  [ok] 文件已安装到 $APP_DIR"\n'
        '\n'
        '# Step 3: pip 依赖\n'
        'echo "[3/5] 安装 Python 依赖..."\n'
        'MIRRORS="https://mirrors.aliyun.com/pypi/simple/ https://pypi.tuna.tsinghua.edu.cn/simple/"\n'
        'for mirror in $MIRRORS; do\n'
        '    $PYTHON -m pip install -i $mirror -r "$APP_DIR/requirements.txt" -q 2>/dev/null && break\n'
        'done\n'
        'echo "  [ok] 依赖安装完成"\n'
        '\n'
        '# Step 4: systemd 服务\n'
        'echo "[4/5] 注册 systemd 服务..."\n'
        'cat > /etc/systemd/system/geometry-ai.service << SERVICEEOF\n'
        '[Unit]\n'
        'Description=Geometry AI Server\n'
        'After=network.target\n'
        '\n'
        '[Service]\n'
        'Type=simple\n'
        'User=root\n'
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
        '# Step 5: 重建索引\n'
        'echo "[5/5] 重建知识库索引..."\n'
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
    print("  + install.sh (路由已修复为 /v1/vector/rebuild)")
    print("  + fix_index.sh (路由已修复为 /v1/vector/rebuild)")

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
        f"Depends: python3 (>= 3.10), python3-pip, systemd\n"
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
    """打包为 zip"""
    version = get_version()
    zip_name = f"geometry-ai-server_ubuntu_v{version}_amd64.zip"
    zip_path = PROJECT_ROOT / zip_name

    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(BUILD_DIR.rglob("*")):
            if file.is_file():
                # 跳过 __pycache__
                if "__pycache__" in str(file) or file.suffix == ".pyc":
                    continue
                arcname = f"geometry-ai-server_{version}_amd64/{file.relative_to(BUILD_DIR)}"
                zf.write(file, arcname)

    size = zip_path.stat().st_size
    print(f"\n  打包完成: {zip_name} ({size/1024/1024:.1f} MB)")

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
