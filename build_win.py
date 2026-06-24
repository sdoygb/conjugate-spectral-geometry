#!/usr/bin/env python3
"""
Geometry AI Server - Windows 安装包构建脚本
用法: python3 build_win.py
"""
import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build_win"
WIN_DIR = PROJECT_ROOT / "windows"

# Python 源码文件
PY_FILES = [
    "server.py", "config.py", "knowledge.py", "models.py",
    "prompts.py", "tools.py", "stream.py", "admin_routes.py",
    "share_routes.py", "auto_teach.py", "start.py", "version.py",
]

# 数据目录
DATA_DIRS = ["articles", "chroma_db", "templates"]

# Python 依赖
REQUIREMENTS = [
    "openai", "flask", "flask-cors", "chromadb", "python-dotenv", "pymysql",
]


def copy_app_files():
    """复制应用文件到 build_win/app/"""
    app_dir = BUILD_DIR / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    print("[复制] Python 源码文件 -> build_win/app/")
    for py_file in PY_FILES:
        src = PROJECT_ROOT / py_file
        dst = app_dir / py_file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  {py_file}")
        else:
            print(f"  [跳过] {py_file} (不存在)")

    print("[复制] 数据目录 -> build_win/app/")
    for data_dir in DATA_DIRS:
        src = PROJECT_ROOT / data_dir
        dst = app_dir / data_dir
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  {data_dir}/")
        else:
            print(f"  [跳过] {data_dir}/ (不存在)")

    # 复制配置文件
    env_example = PROJECT_ROOT / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, app_dir / ".env.example")
        print("[复制] .env.example")


def copy_win_scripts():
    """复制 windows/ 目录下的脚本到 build_win/"""
    print("[复制] Windows 脚本 -> build_win/")
    for f in WIN_DIR.iterdir():
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
Geometry AI Server - Windows 安装说明
============================================================

【全自动安装】
  1. 解压 GeometryAI-Win-Build.zip 到任意目录
  2. 双击 install_win.bat
  3. 脚本会自动：检查 Python、安装依赖、配置 API Key、注册开机自启
  4. 首次运行需要输入 API Key（在 https://platform.deepseek.com 获取）

【手动安装】
  如果全自动安装失败，请按以下步骤操作：

一、环境要求
------------
- Windows 10/11
- Python 3.11+（安装时勾选 "Add Python to PATH"）

二、安装依赖
------------
  cd app
  pip install -r requirements.txt

三、配置
--------
  复制 .env.example 为 .env，填入 API Key

四、启动
--------
  python server.py

五、开机自启（可选）
------------------
  运行 install_win.bat 会自动配置
  或手动将 start_server.bat 放到启动文件夹：
  Win+R 输入 shell:startup

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
  双击 uninstall_win.bat

【卸载】
  1. 双击 uninstall_win.bat
  2. 删除安装目录
"""
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)


def create_zip():
    """打包为 zip（内部带 GeometryAI-Win-Build/ 目录前缀）"""
    zip_name = "GeometryAI-Win-Build.zip"
    zip_path = PROJECT_ROOT / zip_name
    folder_name = "GeometryAI-Win-Build"

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
    print("Geometry AI Server - Windows 安装包构建")
    print(f"构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 清理旧构建
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    copy_app_files()
    copy_win_scripts()
    generate_requirements()
    generate_readme()
    create_zip()

    print()
    print("=" * 60)
    print("构建完成！")
    print()
    print("安装方式:")
    print("  1. 解压 GeometryAI-Win-Build.zip")
    print("  2. 双击 install_win.bat")
    print("  3. 输入 API Key")
    print("  4. 等待安装完成，浏览器自动打开管理界面")
    print("=" * 60)


if __name__ == "__main__":
    main()
