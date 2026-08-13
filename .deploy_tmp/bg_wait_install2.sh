#!/bin/bash
# 等待 open-webui 安装完成，最长 1800 秒
for i in $(seq 1 180); do
  sleep 10
  if grep -q "Successfully installed open-webui" /tmp/owui_install2.log 2>/dev/null; then
    echo "INSTALL_DONE after ~$((i*10))s"
    grep "Successfully installed" /tmp/owui_install2.log | tail -1
    exit 0
  fi
  if ! ps aux | grep "pip install open-webui" | grep -v grep > /dev/null 2>&1; then
    echo "PIP_EXITED at ~$((i*10))s (no process)"
    tail -5 /tmp/owui_install2.log
    exit 1
  fi
done
echo "TIMEOUT_1800s"
tail -3 /tmp/owui_install2.log
