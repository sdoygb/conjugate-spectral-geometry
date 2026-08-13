#!/bin/bash
echo "=== python3.12 位置 ==="
which python3.12 2>/dev/null || ls /usr/bin/python3* 2>/dev/null
echo ""
echo "=== 当前 open-webui.service 完整内容 ==="
cat /etc/systemd/system/open-webui.service
echo ""
echo "=== 备份服务文件 ==="
cp /etc/systemd/system/open-webui.service /root/open-webui.service.bak_$(date +%Y%m%d%H%M%S) && echo "备份完成"
echo ""
echo "=== 磁盘空间 ==="
df -h /usr/local | tail -1
