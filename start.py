#!/usr/bin/env python3
"""
Geometry AI Server 一键启动脚本
自动检测 Python 环境，安装缺失依赖，然后启动服务器。
"""

import subprocess
import sys
import os

# 颜色输出
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════╗
║        Geometry AI Server 启动器              ║
║        几何论 AI 学习平台 一键启动                 ║
╚══════════════════════════════════════════════╝{RESET}
""")

def run(cmd, check=True):
    """运行命令并返回结果"""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)

def check_python_version():
    """检查 Python 版本 >= 3.9"""
    ver = sys.version_info
    print(f"{CYAN}[1/5] Python 版本检查{RESET}")
    print(f"      当前版本: Python {ver.major}.{ver.minor}.{ver.micro}")
    if ver.major < 3 or (ver.major == 3 and ver.minor < 9):
        print(f"{RED}      ✗ 需要 Python 3.9 或更高版本{RESET}")
        print(f"      请访问 https://www.python.org/downloads/ 下载安装")
        sys.exit(1)
    print(f"{GREEN}      ✓ Python 版本满足要求{RESET}")
    return True

def check_pip():
    """检查 pip 是否可用"""
    print(f"{CYAN}[2/5] pip 检查{RESET}")
    result = run("pip3 --version", check=False)
    if result.returncode != 0:
        result = run("pip --version", check=False)
    if result.returncode != 0:
        print(f"{YELLOW}      ⚠ pip 未找到，尝试安装...{RESET}")
        run(f"{sys.executable} -m ensurepip --upgrade")
    print(f"{GREEN}      ✓ pip 可用{RESET}")

def install_package(package, import_name=None):
    """安装单个包"""
    if import_name is None:
        import_name = package
    try:
        __import__(import_name)
        print(f"{GREEN}      ✓ {package} 已安装{RESET}")
        return True
    except ImportError:
        print(f"{YELLOW}      ⚠ {package} 未安装，正在安装...{RESET}")
        result = run(f"{sys.executable} -m pip install {package} --break-system-packages", check=False)
        if result.returncode == 0:
            print(f"{GREEN}      ✓ {package} 安装成功{RESET}")
            return True
        else:
            # 尝试不带 --break-system-packages
            result = run(f"{sys.executable} -m pip install {package}", check=False)
            if result.returncode == 0:
                print(f"{GREEN}      ✓ {package} 安装成功{RESET}")
                return True
            print(f"{RED}      ✗ {package} 安装失败: {result.stderr[:200]}{RESET}")
            return False

def check_dependencies():
    """检查并安装所有依赖"""
    print(f"{CYAN}[3/5] 依赖检查与安装{RESET}")
    deps = [
        ("openai", "openai"),
        ("flask", "flask"),
        ("flask-cors", "flask_cors"),
        ("chromadb", "chromadb"),
    ]
    all_ok = True
    for package, import_name in deps:
        if not install_package(package, import_name):
            all_ok = False
    return all_ok

def check_env():
    """检查环境变量"""
    print(f"{CYAN}[4/5] 环境变量检查{RESET}")
    api_key = os.environ.get("KIMI_API_KEY", "")
    if not api_key:
        print(f"{YELLOW}      ⚠ KIMI_API_KEY 未设置{RESET}")
        print(f"      请设置环境变量：")
        print(f"        export KIMI_API_KEY=\"你的API密钥\"")
        print(f"      或在启动时传入：")
        print(f"        KIMI_API_KEY=xxx python3 server.py")
        print(f"")
        print(f"      免费注册：https://platform.moonshot.cn")
    else:
        print(f"{GREEN}      ✓ KIMI_API_KEY 已设置 ({api_key[:8]}...){RESET}")

    # 检查 chroma_db 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chroma_path = os.path.join(script_dir, "chroma_db")
    if os.path.exists(chroma_path):
        print(f"{GREEN}      ✓ 向量数据库已存在 ({chroma_path}){RESET}")
    else:
        print(f"{YELLOW}      ⚠ 向量数据库不存在，首次启动将自动构建索引{RESET}")

    # 检查 articles 目录
    articles_path = os.path.join(script_dir, "articles")
    if os.path.exists(articles_path):
        count = len([f for f in os.listdir(articles_path) if f.endswith('.md')])
        print(f"{GREEN}      ✓ 文章目录已存在 ({count} 篇){RESET}")
    else:
        print(f"{YELLOW}      ⚠ articles 目录不存在{RESET}")

def start_server():
    """启动服务器"""
    print(f"{CYAN}[5/5] 启动服务器{RESET}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "server.py")

    if not os.path.exists(server_script):
        print(f"{RED}      ✗ 找不到主程序: {server_script}{RESET}")
        sys.exit(1)

    print(f"{GREEN}      ✓ 启动中...{RESET}")
    print(f"")
    print(f"{BOLD}      访问地址: http://localhost:5000{RESET}")
    print(f"{BOLD}      API 文档: http://localhost:5000/v1/openapi.json{RESET}")
    print(f"{BOLD}      健康检查: http://localhost:5000/health{RESET}")
    print(f"")
    print(f"      按 Ctrl+C 停止服务器")
    print(f"{CYAN}      ─────────────────────────────────────{RESET}")

    # 启动服务器
    os.execv(sys.executable, [sys.executable, server_script])

def main():
    print_banner()

    steps = [
        check_python_version,
        check_pip,
        check_dependencies,
        check_env,
    ]

    for step in steps:
        try:
            step()
        except Exception as e:
            print(f"{RED}      ✗ 检查失败: {e}{RESET}")
            sys.exit(1)

    start_server()

if __name__ == "__main__":
    main()
