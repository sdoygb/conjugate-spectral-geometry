#!/bin/bash
echo "=== STT_DIAG 诊断日志 ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "5 min ago" --no-pager 2>/dev/null | grep -E "STT_DIAG|transcrib|422|Converted|Chunk paths" | tail -25
