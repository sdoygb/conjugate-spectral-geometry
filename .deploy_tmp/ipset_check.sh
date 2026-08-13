#!/bin/bash
echo "=== ipset 集合列表 ==="
ipset list -n 2>/dev/null
echo ""
echo "=== in_bt_user_drop_ipset 成员 ==="
ipset list in_bt_user_drop_ipset 2>/dev/null
echo ""
echo "=== out_bt_user_drop_ipset 成员 ==="
ipset list out_bt_user_drop_ipset 2>/dev/null
echo ""
echo "=== 各集合成员数 ==="
for s in $(ipset list -n 2>/dev/null); do
  cnt=$(ipset list $s 2>/dev/null | grep -cE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
  echo "$s: $cnt 个 IP"
done
echo ""
echo "=== IN_BT 链完整规则 ==="
iptables -L IN_BT -n --line-numbers 2>/dev/null | head -30
echo ""
echo "=== 宝塔防火墙日志（封禁记录） ==="
ls /www/server/panel/plugin/btwaf* 2>/dev/null | head -5
grep -r "drop_ipset\|封禁" /www/server/panel/logs/*.log 2>/dev/null | tail -10
