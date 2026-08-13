#!/bin/bash
echo "=== 写入测试 /root/.cache/pip (500MB) ==="
dd if=/dev/zero of=/root/.cache/pip/test500.bin bs=1M count=500 2>&1 | tail -1
rm -f /root/.cache/pip/test500.bin
echo "=== 写入测试 /tmp (500MB, tmpfs) ==="
dd if=/dev/zero of=/tmp/test500.bin bs=1M count=500 2>&1 | tail -1
rm -f /tmp/test500.bin
echo "=== tmpfs 现状 ==="
df -h /tmp /dev/shm /run 2>/dev/null
echo "=== 缓存结构 ==="
du -sh /root/.cache/pip/* 2>/dev/null | sort -rh | head -5
echo "=== 大文件残留 /tmp ==="
ls -la /tmp | head -8
