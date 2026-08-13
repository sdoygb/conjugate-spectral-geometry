#!/bin/bash
sleep 100
journalctl -u geometry-ai --no-pager -n 30 2>&1 | grep -E "VECTOR|STARTUP|ERROR|索引" | tail -12
echo "---"
systemctl is-active geometry-ai
