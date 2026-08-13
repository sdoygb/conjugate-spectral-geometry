#!/bin/bash
echo "=== 原始日志最后15行 ==="
journalctl -u geometry-ai --no-pager -n 15 2>&1 | tail -15
echo "=== 状态 ==="
systemctl is-active geometry-ai
