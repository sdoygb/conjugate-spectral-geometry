#!/usr/bin/env python3
"""
Geometry AI Server - macOS 安装包构建脚本
用法: python3 build_mac.py [--python-dir /path/to/python]
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build_mac"
MAC_DIR = PROJECT_ROOT / "mac"

# Python 源码文件
PY_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
]

# 数据目录
DATA_DIRS = ["articles", "templates"]

# Python 依赖
REQUIREMENTS = [
    "openai", "flask", "flask-cors", "chromadb", "python-dotenv", "pymysql",
]


def copy_app_files():
    """复制应用文件到 build_mac/app/"""
    app_dir = BUILD_DIR / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    # 源码在 app/ 子目录下
    APP_SRC = PROJECT_ROOT / "app"

    print("[复制] Python 源码文件 -> build_mac/app/")
    for py_file in PY_FILES:
        src = APP_SRC / py_file
        dst = app_dir / py_file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  {py_file}")
        else:
            print(f"  [跳过] {py_file} (不存在)")

    print("[复制] 数据目录 -> build_mac/app/")
    for data_dir in DATA_DIRS:
        src = APP_SRC / data_dir
        dst = app_dir / data_dir
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  {data_dir}/")
        else:
            print(f"  [跳过] {data_dir}/ (不存在)")

    # 复制配置文件
    env_example = APP_SRC / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env.example")
        print("[复制] .env.example")


def copy_mac_scripts():
    """复制 mac/ 目录下的脚本到 build_mac/"""
    print("[复制] macOS 脚本 -> build_mac/")
    for f in MAC_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, BUILD_DIR / f.name)
            print(f"  {f.name}")


def generate_requirements():
    """生成 requirements.txt"""
    req_file = BUILD_DIR / "app" / "requirements.txt"
    print("[生成] requirements.txt")
    with open(req_file, "w", encoding="utf-8") as f:
        f.write("# Geometry AI Server - Python 依赖\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for req in REQUIREMENTS:
            f.write(f"{req}\n")


def generate_readme():
    """生成安装说明"""
    readme_file = BUILD_DIR / "README.txt"
    print("[生成] README.txt")
    content = """\
============================================================
Geometry AI Server - macOS 安装说明
============================================================

【全自动安装】
  1. 双击 install_mac.sh（或在终端执行: bash install_mac.sh）
  2. 脚本会自动：检查 Python、安装依赖、配置 API Key、注册开机自启
  3. 首次运行需要输入 API Key（在 https://platform.deepseek.com 获取）

【手动安装】
  如果全自动安装失败，请按以下步骤操作：

一、环境要求
------------
- macOS 12+ (Monterey 或更高)
- Python 3.9+ (系统自带或 Homebrew 安装)

二、安装依赖
------------
  cd app
  pip3 install -r requirements.txt

三、配置
--------
  复制 .env.example 为 .env，填入 API Key

四、启动
--------
  python3 server.py

五、开机自启（可选）
------------------
  运行 install_mac.sh 会自动配置 launchd 服务
  或手动: launchctl load ~/Library/LaunchAgents/com.geometryai.server.plist

【管理界面】
  http://localhost:5000/admin

【聊天界面】
  http://localhost:8080

  首次打开需要：
  1. 创建管理员账号（注册）
  2. 登录后，点击左下角头像 → Settings（设置）
  3. 左侧选 Connections（连接）
  4. 确认 OpenAI API 连接：
     - URL: http://localhost:5000/v1
     - Key: 随便填（如 sk-123）
  5. 回到聊天页面，点左上角模型下拉框
  6. 选择 deepseek-v4-pro（主力模型）或 deepseek-v4-flash（快速模型）
  7. 开始聊天！

【停止服务】
  launchctl unload ~/Library/LaunchAgents/com.geometryai.server.plist
  launchctl unload ~/Library/LaunchAgents/com.geometryai.webui.plist

【卸载】
  1. launchctl unload ~/Library/LaunchAgents/com.geometryai.server.plist
  2. rm ~/Library/LaunchAgents/com.geometryai.server.plist
  3. 删除安装目录
"""
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)


def create_zip():
    """打包为 zip（内部带 GeometryAI-Mac-Build/ 目录前缀）"""
    # 从 version.py 读取版本号
    version = "unknown"
    version_file = PROJECT_ROOT / "app" / "version.py"
    if version_file.exists():
        for vl in version_file.read_text(encoding="utf-8").splitlines():
            if vl.strip().startswith("VERSION"):
                version = vl.split(chr(34))[1]
                break


    """打包为 zip（内部带 GeometryAI-Mac-Build/ 目录前缀）"""
    zip_name = f"GeometryAI-Mac-Build-v{version}.zip"
    zip_path = PROJECT_ROOT / zip_name
    folder_name = "GeometryAI-Mac-Build"

    print(f"\n[打包] 创建 {zip_name} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in BUILD_DIR.rglob("*"):
            if file_path.is_file():
                arcname = Path(folder_name) / file_path.relative_to(BUILD_DIR)
                zf.write(file_path, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[完成] 打包完成: {zip_path} ({size_mb:.1f} MB)")


def main():
    print("=" * 60)
    print("Geometry AI Server - macOS 安装包构建")
    print(f"构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 清理旧构建
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    copy_app_files()
    copy_mac_scripts()
    generate_requirements()
    generate_readme()
    create_zip()

    print()
    print("=" * 60)
    print("构建完成！")
    print()
    print("安装方式:")
    print("  1. 解压 GeometryAI-Mac-Build.zip")
    print("  2. 双击 install_mac.sh")
    print("  3. 输入 API Key")
    print("  4. 等待安装完成，浏览器自动打开管理界面")
    print("=" * 60)


if __name__ == "__main__":
    main()
