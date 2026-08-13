#!/bin/bash
# 后台轮询：写结果到文件，立即返回
nohup bash -c 'sleep 90; journalctl -u geometry-ai --no-pager -n 30 > /tmp/poll_out.txt 2>&1; systemctl is-active geometry-ai >> /tmp/poll_out.txt 2>&1' > /dev/null 2>&1 &
echo "BG_POLL_STARTED"
