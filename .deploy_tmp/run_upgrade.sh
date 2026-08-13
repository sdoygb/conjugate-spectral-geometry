#!/bin/bash
nohup bash -c "echo 'ab640815.' | sudo -S bash /tmp/upgrade_webui.sh > /tmp/webui_upgrade.log 2>&1" &
echo "UPGRADE_STARTED pid=$!"
sleep 3
echo "--- 初始日志 ---"
cat /tmp/webui_upgrade.log 2>/dev/null | head -5
