from __future__ import annotations
"""强制使用 pysqlite3 替代系统低版本 sqlite3

ChromaDB 需要 sqlite3 >= 3.35.0，Ubuntu 20.04 系统自带 3.31.1。
将此模块在 server.py 等依赖 ChromaDB 的文件之前导入即可。
"""
import sys

# 检查当前系统 sqlite3 版本
import sqlite3 as _sys_sqlite3
_sys_ver = _sys_sqlite3.sqlite_version_info

if _sys_ver < (3, 35, 0):
    try:
        # 尝试用 pysqlite3 替换
        import pysqlite3 as _new_sqlite3
        _new_ver = _new_sqlite3.sqlite_version_info
        if _new_ver >= (3, 35, 0):
            sys.modules['sqlite3'] = _new_sqlite3
            print(f'[ok] sqlite3 {_sys_sqlite3.sqlite_version} -> {_new_sqlite3.sqlite_version}')
        else:
            print(f'[!] pysqlite3 版本也过低 ({_new_sqlite3.sqlite_version}), 仍使用系统版本')
    except ImportError:
        print(f'[!] pysqlite3 未安装, 使用系统 sqlite3 {_sys_sqlite3.sqlite_version}')
        print('    ChromaDB 可能需要 sqlite3 >= 3.35.0, 安装: pip install pysqlite3-binary')
