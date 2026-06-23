#!/usr/bin/env python3
"""
build_windows.py - Windows 安装包构建脚本

在 macOS/Linux 上准备 Windows 安装包的文件结构。
运行此脚本后，将 build/ 目录复制到 Windows 机器上，
使用 Inno Setup 编译 installer.iss 即可生成安装程序。

用法:
    python build_windows.py [--python-dir /path/to/windows/python]

参数:
    --python-dir   Windows 嵌入式 Python 目录路径（可选）
                   如果不指定，需要用户自行准备并放入 build/python/
"""

import os
import sys
import shutil
import zipfile
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================
# 项目根目录（本脚本所在目录）
PROJECT_ROOT = Path(__file__).parent.resolve()

# 构建输出目录
BUILD_DIR = PROJECT_ROOT / "build"

# 最终打包文件名
OUTPUT_ZIP = PROJECT_ROOT / "GeometryAI-Windows-Build.zip"

# 需要复制到 build/app/ 的 Python 模块文件
PY_FILES = [
    "server.py",
    "config.py",
    "knowledge.py",
    "models.py",
    "prompts.py",
    "tools.py",
    "stream.py",
    "admin_routes.py",
    "auto_teach.py",
    "start.py",
]

# 需要复制到 build/app/ 的目录
COPY_DIRS = [
    "articles",
    "chroma_db",
    "templates",
]

# 需要复制到 build/ 的其他文件
COPY_FILES = [
    ".env.example",
]

# Python 依赖列表
REQUIREMENTS = [
    "openai>=1.0.0",
    "flask>=3.0.0",
    "flask-cors>=4.0.0",
    "chromadb>=0.4.0",
    "requests>=2.31.0",
    "werkzeug>=3.0.0",
]


def clean_build_dir():
    """清理旧的构建目录"""
    if BUILD_DIR.exists():
        print(f"[清理] 删除旧的构建目录: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def copy_python_files():
    """复制 Python 源码文件到 build/app/"""
    app_dir = BUILD_DIR / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    print("[复制] Python 源码文件 -> build/app/")
    for py_file in PY_FILES:
        src = PROJECT_ROOT / py_file
        dst = app_dir / py_file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  {py_file}")
        else:
            print(f"  [警告] 未找到: {py_file}")


def copy_directories():
    """复制 articles/、chroma_db/、templates/ 等目录到 build/app/"""
    app_dir = BUILD_DIR / "app"

    print("[复制] 数据目录 -> build/app/")
    for dir_name in COPY_DIRS:
        src = PROJECT_ROOT / dir_name
        dst = app_dir / dir_name
        if src.exists():
            shutil.copytree(src, dst)
            print(f"  {dir_name}/")
        else:
            print(f"  [警告] 未找到目录: {dir_name}/")


def copy_extra_files():
    """复制 .env.example 等配置文件到 build/app/"""
    app_dir = BUILD_DIR / "app"

    print("[复制] 配置文件 -> build/app/")
    for file_name in COPY_FILES:
        src = PROJECT_ROOT / file_name
        dst = app_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  {file_name}")
        else:
            print(f"  [警告] 未找到: {file_name}")


def copy_python_runtime(python_dir=None):
    """复制 Windows 嵌入式 Python 到 build/python/

    如果指定了 python_dir，则从该目录复制。
    否则创建占位目录并提示用户手动放入。
    """
    python_build_dir = BUILD_DIR / "python"

    if python_dir:
        # 用户指定了 Python 目录，直接复制
        python_src = Path(python_dir)
        if not python_src.exists():
            print(f"[错误] Python 目录不存在: {python_src}")
            sys.exit(1)
        print(f"[复制] Python 运行时: {python_src} -> build/python/")
        shutil.copytree(python_src, python_build_dir)
    else:
        # 创建占位目录，提示用户
        python_build_dir.mkdir(parents=True, exist_ok=True)
        print("[提示] 未指定 Python 目录，已创建 build/python/ 占位目录")
        print("       请将 Windows 嵌入式 Python 放入 build/python/")


def copy_windows_scripts():
    """复制 windows/ 目录下的批处理脚本到 build/"""
    windows_dir = PROJECT_ROOT / "windows"

    print("[复制] Windows 脚本 -> build/")
    for bat_file in windows_dir.glob("*.bat"):
        shutil.copy2(bat_file, BUILD_DIR / bat_file.name)
        print(f"  {bat_file.name}")


def copy_nssm():
    """检查并提示 NSSM 放置"""
    nssm_path = BUILD_DIR / "nssm.exe"
    if not nssm_path.exists():
        print("[提示] 未找到 nssm.exe")
        print("       请将 nssm.exe 放入 build/ 目录")
        print("       下载地址: https://nssm.cc/download")


def generate_requirements():
    """生成 requirements.txt 到 build/app/"""
    req_file = BUILD_DIR / "app" / "requirements.txt"

    print("[生成] requirements.txt")
    with open(req_file, "w", encoding="utf-8") as f:
        f.write("# Geometry AI Server - Python 依赖\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for req in REQUIREMENTS:
            f.write(f"{req}\n")


def generate_readme():
    """生成构建说明 README 到 build/README.txt"""
    readme_file = BUILD_DIR / "README.txt"

    print("[生成] README.txt")
    content = """\
============================================================
Geometry AI Server - Windows 安装包构建说明
============================================================

一、前置准备
------------
1. 准备 Windows 嵌入式 Python (Embedded Python)
   - 下载地址: https://www.python.org/downloads/windows/
   - 选择 "Windows embeddable package (64-bit)"
   - 解压后将全部内容放入 build/python/ 目录

2. 安装 Python 依赖
   - 在 Windows 上打开命令提示符
   - cd build/python
   - .\\python.exe -m pip install --target=. -r ..\\app\\requirements.txt

3. 下载 NSSM (Non-Sucking Service Manager)
   - 下载地址: https://nssm.cc/download
   - 将 nssm.exe 放入 build/ 目录

二、编译安装程序
----------------
1. 安装 Inno Setup 6.x
   - 下载地址: https://jrsoftware.org/isdl.php

2. 将整个 build/ 目录和 windows/installer.iss 复制到 Windows 机器

3. 用 Inno Setup 打开 installer.iss，点击编译 (Build)

4. 编译完成后，在 installer_output/ 目录找到安装程序 .exe

三、文件结构
------------
build/
  python/          - Windows 嵌入式 Python 运行时（需手动放入）
  app/             - 应用程序文件
    server.py      - 主服务入口
    config.py      - 配置模块
    knowledge.py   - 知识库模块
    models.py      - 数据模型
    prompts.py     - 提示词系统
    tools.py       - 工具函数
    stream.py      - 流式输出
    admin_routes.py - 管理界面路由
    auto_teach.py  - 自动教学
    start.py       - 启动辅助
    articles/      - 知识库文章
    chroma_db/     - 向量数据库
    templates/     - HTML 模板
    requirements.txt - Python 依赖列表
    .env.example   - 环境变量示例
  nssm.exe         - Windows 服务管理器（需手动放入）
  install_service.bat  - 服务注册脚本
  uninstall_service.bat - 服务卸载脚本
  start.bat        - 手动启动脚本

四、安装后配置
--------------
安装程序会引导你输入 API Key 和 Base URL。
配置文件保存在安装目录的 app/.env 中。

管理界面: http://localhost:5000/admin

============================================================
"""
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(content)


def create_zip():
    """将 build/ 目录打包为 zip 文件"""
    print(f"\n[打包] 创建 {OUTPUT_ZIP.name} ...")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in BUILD_DIR.rglob("*"):
            if file_path.is_file():
                # 计算相对路径
                arcname = file_path.relative_to(BUILD_DIR)
                zf.write(file_path, arcname)

    # 显示文件大小
    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"[完成] 打包完成: {OUTPUT_ZIP} ({size_mb:.1f} MB)")


def main():
    """主构建流程"""
    parser = argparse.ArgumentParser(
        description="Geometry AI Server Windows 安装包构建脚本"
    )
    parser.add_argument(
        "--python-dir",
        type=str,
        default=None,
        help="Windows 嵌入式 Python 目录路径（可选）"
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="不打包为 zip 文件"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Geometry AI Server - Windows 安装包构建")
    print(f"构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 步骤 1: 清理旧构建
    clean_build_dir()

    # 步骤 2: 复制 Python 源码
    copy_python_files()

    # 步骤 3: 复制数据目录
    copy_directories()

    # 步骤 4: 复制配置文件
    copy_extra_files()

    # 步骤 5: 复制 Windows 脚本
    copy_windows_scripts()

    # 步骤 6: 处理 Python 运行时
    copy_python_runtime(args.python_dir)

    # 步骤 7: 检查 NSSM
    copy_nssm()

    # 步骤 8: 生成 requirements.txt
    generate_requirements()

    # 步骤 9: 生成 README
    generate_readme()

    # 步骤 10: 打包
    if not args.no_zip:
        create_zip()

    print()
    print("=" * 60)
    print("构建完成！")
    print()
    print("后续步骤:")
    print("  1. 将 build/ 目录复制到 Windows 机器")
    print("  2. 放入 Windows 嵌入式 Python 到 build/python/")
    print("  3. 放入 nssm.exe 到 build/")
    print("  4. 安装 Python 依赖: build/python/python.exe -m pip install --target=. -r build/app/requirements.txt")
    print("  5. 用 Inno Setup 编译 windows/installer.iss")
    print("=" * 60)


if __name__ == "__main__":
    main()
