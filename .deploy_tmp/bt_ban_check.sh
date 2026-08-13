#!/bin/bash
echo "=== 1. fail2ban 状态 ==="
fail2ban-client status 2>/dev/null || echo "fail2ban 未安装/未运行"
for j in $(fail2ban-client status 2>/dev/null | grep "Jail list" | sed 's/.*:\s*//' | tr ',' ' '); do
  echo "--- jail: $j ---"
  fail2ban-client status $j 2>/dev/null | grep -E "banned|Currently|Total"
done
echo ""
echo "=== 2. iptables INPUT 链（完整带行号） ==="
iptables -L INPUT -n --line-numbers 2>/dev/null | head -50
echo ""
echo "=== 3. iptables 全部 DROP/REJECT 规则 ==="
iptables -S 2>/dev/null | grep -E "DROP|REJECT" | head -30
echo ""
echo "=== 4. 宝塔 IP 封禁文件 ==="
ls /www/server/panel/data/*.json 2>/dev/null | head -20
echo "--- v4ip.json ---"
cat /www/server/panel/data/v4ip.json 2>/dev/null | head -10
echo "--- v4ipv6.json ---"
cat /www/server/panel/data/v4ipv6.json 2>/dev/null | head -5
echo ""
echo "=== 5. 当前 22 端口连接（来源 IP） ==="
ss -tn state established 2>/dev/null | grep ":22" | head -10
echo ""
echo "=== 6. 最近登录记录 ==="
last -n 10 2>/dev/null | head -12
echo ""
echo "=== 7. fail2ban 日志（最近封禁） ==="
tail -25 /var/log/fail2ban.log 2>/dev/null || echo "无 fail2ban 日志"
echo ""
echo "=== 8. ufw 完整规则 ==="
ufw status numbered 2>/dev/null | head -40
