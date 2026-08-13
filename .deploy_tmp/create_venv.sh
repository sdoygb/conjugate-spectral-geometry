#!/bin/bash
set -e
echo "=== 1. 备份服务文件 ==="
cp /etc/systemd/system/open-webui.service /root/open-webui.service.bak_$(date +%Y%m%d%H%M%S)
echo "备份完成: $(ls /root/open-webui.service.bak_* | tail -1)"
echo ""
echo "=== 2. 创建独立 venv ==="
/usr/bin/python3.12 -m venv /usr/local/open-webui-venv
echo "venv 创建完成: /usr/local/open-webui-venv"
echo ""
echo "=== 3. 升级 pip ==="
/usr/local/open-webui-venv/bin/pip install --upgrade pip 2>&1 | tail -1
echo ""
echo "=== 4. 安装 open-webui 0.11.0（后台） ==="
nohup /usr/local/open-webui-venv/bin/pip install open-webui==0.11.0 > /tmp/owui_install.log 2>&1 &
echo "pip 安装已后台启动 pid=$!"
echo "日志: /tmp/owui_install.log"
