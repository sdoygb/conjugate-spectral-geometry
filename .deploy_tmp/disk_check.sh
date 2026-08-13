#!/bin/bash
echo "=== pip 错误日志全文（尾部30行） ==="
tail -30 /tmp/owui_install3.log
echo ""
echo "=== root 缓存实际大小 ==="
du -sh /root/.cache/pip 2>&1 | tail -1
echo ""
echo "=== 大目录盘点（>1G） ==="
du -x -h --max-depth=1 / 2>/dev/null | sort -rh | head -12
echo ""
echo "=== docker 大小 ==="
du -sh /var/lib/docker 2>/dev/null | tail -1
echo ""
echo "=== venv 实际大小 ==="
du -sh /usr/local/open-webui-venv /usr/local/geometry-ai 2>/dev/null
echo ""
echo "=== 所有挂载点 ==="
df -hT | grep -vE "tmpfs|udev|loop" 
echo ""
echo "=== 根分区 inode 与残留 ==="
df -i / | tail -1
