#!/bin/bash
echo "=== venv_setup.log 尾部 ==="
tail -6 /tmp/venv_setup.log 2>/dev/null
echo ""
echo "=== owui_install.log 尾部 ==="
tail -6 /tmp/owui_install.log 2>/dev/null
echo ""
echo "=== pip 进程 ==="
ps aux | grep "pip install" | grep -v grep | head -2 || echo "无 pip 进程"
echo ""
echo "=== venv 大小 ==="
du -sh /usr/local/open-webui-venv 2>/dev/null
