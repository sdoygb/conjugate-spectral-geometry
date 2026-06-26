#!/usr/bin/env python3
"""
Geometry AI Server 一键启动脚本
自动检测 Python 环境，安装缺失依赖，然后启动服务器。
"""

import subprocess
import sys
import os

# 自动加载 .env 文件（如果存在）
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_file = os.path.join(_script_dir, '.env')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _, _val = _line.partition('=')
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

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
    print(f"{CYAN}[1/6] Python 版本检查{RESET}")
    print(f"      当前版本: Python {ver.major}.{ver.minor}.{ver.micro}")
    if ver.major < 3 or (ver.major == 3 and ver.minor < 9):
        print(f"{RED}      ✗ 需要 Python 3.9 或更高版本{RESET}")
        print(f"      请访问 https://www.python.org/downloads/ 下载安装")
        sys.exit(1)
    print(f"{GREEN}      ✓ Python 版本满足要求{RESET}")
    return True

def check_pip():
    """检查 pip 是否可用"""
    print(f"{CYAN}[2/6] pip 检查{RESET}")
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
    print(f"{CYAN}[3/6] 依赖检查与安装{RESET}")
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
    print(f"{CYAN}[4/6] 环境变量检查{RESET}")
    api_key = os.environ.get("GAI_API_KEY", "")
    if not api_key:
        print(f"{YELLOW}      ⚠ GAI_API_KEY 未设置{RESET}")
        print(f"      请设置环境变量：")
        print(f"        export GAI_API_KEY=\"你的API密钥\"")
        print(f"      或在启动时传入：")
        print(f"        GAI_API_KEY=xxx python3 server.py")
        print(f"")
        print(f"      免费注册：https://platform.deepseek.com")
    else:
        print(f"{GREEN}      ✓ GAI_API_KEY 已设置 ({api_key[:8]}...){RESET}")

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
    print(f"{CYAN}[5/6] 准备运行目录{RESET}")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 运行目录：优先使用环境变量，否则使用项目目录
    run_dir = os.getenv('GEOMETRY_AI_HOME', script_dir)

    # 如果运行目录和源目录不同，需要同步文件
    source_dir = script_dir
    if os.path.realpath(run_dir) != os.path.realpath(source_dir):
        # 运行目录和源目录不同，需要同步文件
        py_files = [f for f in os.listdir(source_dir) if f.endswith('.py') and f != 'auto_teach.py']
        if os.path.exists(run_dir):
            import shutil
            synced = 0
            for f in py_files:
                src = os.path.join(source_dir, f)
                dst = os.path.join(run_dir, f)
                if os.path.realpath(src) == os.path.realpath(dst):
                    continue
                shutil.copy2(src, dst)
                synced += 1
            if synced > 0:
                print(f"{GREEN}      ✓ 已同步 {synced} 个文件到 {run_dir}{RESET}")
            else:
                print(f"{GREEN}      ✓ 文件已是最新{RESET}")
    else:
        print(f"{GREEN}      ✓ 运行目录与源目录相同，无需同步{RESET}")

    print(f"{CYAN}[6/6] 启动服务器{RESET}")
    server_script = os.path.join(run_dir, "server.py")

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
    print(f"      文件变化时自动重启（watchdog 模式）")
    print(f"{CYAN}      ─────────────────────────────────────{RESET}")

    # watchdog 模式：检测源文件变化，自动同步并重启
    import time as _time
    py_files_to_watch = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.py') and f != 'auto_teach.py']
    # 记录每个文件的最后修改时间
    file_mtimes = {f: os.path.getmtime(f) for f in py_files_to_watch if os.path.exists(f)}

    while True:
        # 同步文件
        changed = False
        for f in py_files_to_watch:
            if not os.path.exists(f):
                continue
            dst = os.path.join(run_dir, os.path.basename(f))
            if os.path.realpath(f) == os.path.realpath(dst):
                continue
            current_mtime = os.path.getmtime(f)
            if current_mtime != file_mtimes.get(f):
                file_mtimes[f] = current_mtime
                try:
                    shutil.copy2(f, dst)
                    changed = True
                    print(f"{YELLOW}[WATCHDOG] 已同步: {os.path.basename(f)}{RESET}")
                except Exception as e:
                    print(f"{RED}[WATCHDOG] 同步失败: {e}{RESET}")

        # 启动服务器子进程
        proc = subprocess.Popen(
            [sys.executable, server_script],
            cwd=run_dir
        )
        try:
            # 每 3 秒检查一次文件变化
            while proc.poll() is None:
                _time.sleep(3)
                for f in py_files_to_watch:
                    if not os.path.exists(f):
                        continue
                    if os.path.getmtime(f) != file_mtimes.get(f):
                        file_mtimes[f] = os.path.getmtime(f)
                        dst = os.path.join(run_dir, os.path.basename(f))
                        if os.path.realpath(f) != os.path.realpath(dst):
                            try:
                                shutil.copy2(f, dst)
                                print(f"{YELLOW}[WATCHDOG] 文件变化，同步: {os.path.basename(f)}{RESET}")
                            except Exception as e:
                                print(f"{RED}[WATCHDOG] 同步失败: {e}{RESET}")
                        # 杀掉旧进程，重启
                        print(f"{YELLOW}[WATCHDOG] 检测到变化，重启服务器...{RESET}")
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        changed = True
                        break
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            print(f"\n{CYAN}服务器已停止{RESET}")
            break

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
