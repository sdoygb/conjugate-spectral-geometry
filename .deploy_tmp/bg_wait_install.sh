#!/bin/bash
# 等待 open-webui 安装完成，最长 1500 秒
for i in $(seq 1 150); do
  sleep 10
  if grep -q "Successfully installed open-webui" /tmp/owui_install.log 2>/dev/null; then
    echo "INSTALL_DONE after ~$((i*10))s" > /tmp/install_wait.txt
    grep "Successfully installed" /tmp/owui_install.log | tail -1 >> /tmp/install_wait.txt
    echo "open-webui 版本: $(/usr/local/open-webui-venv/bin/pip show open-webui 2>/dev/null | head -2 | tail -1)" >> /tmp/install_wait.txt
    echo "chromadb 版本: $(/usr/local/open-webui-venv/bin/pip show chromadb 2>/dev/null | head -2 | tail -1)" >> /tmp/install_wait.txt
    exit 0
  fi
  if grep -qiE "ERROR: (Could not find|No matching|pip's dependency)" /tmp/owui_install.log 2>/dev/null; then
    echo "INSTALL_ERROR at ~$((i*10))s" > /tmp/install_wait.txt
    grep -iE "ERROR" /tmp/owui_install.log | tail -8 >> /tmp/install_wait.txt
    exit 1
  fi
done
echo "TIMEOUT_1500s" > /tmp/install_wait.txt
tail -3 /tmp/owui_install.log >> /tmp/install_wait.txt
