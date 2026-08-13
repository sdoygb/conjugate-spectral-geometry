#!/bin/bash
echo "=== 1. 面板端口监听 ==="
ss -tlnp 2>/dev/null | grep -E ':888[0-9]' || echo "888x 端口无监听"
echo ""
echo "=== 2. 宝塔服务状态 ==="
/etc/init.d/bt status 2>&1 | head -8
echo ""
echo "=== 3. 面板进程 ==="
ps aux | grep -iE 'BT-Panel|btpanel|panel' | grep -v grep | head -5
echo ""
echo "=== 4. 面板端口配置 ==="
cat /www/server/panel/data/port.pl 2>/dev/null || echo "无 port.pl"
echo ""
echo "=== 5. 安全入口 ==="
cat /www/server/panel/data/admin_path.pl 2>/dev/null || echo "无 admin_path.pl（未设置安全入口）"
echo ""
echo "=== 6. 防火墙状态 ==="
which ufw >/dev/null 2>&1 && ufw status 2>/dev/null | head -5
echo "--- iptables INPUT ---"
iptables -L INPUT -n 2>/dev/null | head -15
echo ""
echo "=== 7. 面板日志（最近） ==="
ls -lt /www/server/panel/logs/ 2>/dev/null | head -5
tail -15 /www/server/panel/logs/error.log 2>/dev/null || echo "无 error.log"
echo ""
echo "=== 8. 本机访问测试 ==="
timeout 5 bash -c 'echo > /dev/tcp/127.0.0.1/8888' 2>/dev/null && echo "127.0.0.1:8888 TCP 可连" || echo "127.0.0.1:8888 不可连"
echo ""
echo "=== 9. 面板相关服务 ==="
systemctl list-units --type=service 2>/dev/null | grep -iE 'bt|panel' | head -5
echo ""
echo "=== 10. 磁盘与系统负载 ==="
df -h / | tail -1
uptime
