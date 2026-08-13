#!/bin/bash
echo "=== 1. 17995 端口监听 ==="
ss -tlnp 2>/dev/null | grep 17995 || echo "17995 未监听"
echo ""
echo "=== 2. ufw 完整规则 ==="
ufw status numbered 2>/dev/null | head -30
echo ""
echo "=== 3. 宝塔防火墙链 ==="
iptables -L IN_BT -n 2>/dev/null | head -20
echo ""
echo "=== 4. 本机 HTTP 访问测试（带安全入口） ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 http://127.0.0.1:17995/sdoygb
echo ""
echo "=== 5. 本机 IP 访问测试 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 http://192.168.1.88:17995/sdoygb
echo ""
echo "=== 6. 面板绑定限制 ==="
cat /www/server/panel/data/userInfo.json 2>/dev/null | head -5
cat /www/server/panel/data/bind.pl 2>/dev/null && echo "(bind.pl 存在)" || echo "无 bind.pl"
echo ""
echo "=== 7. 面板版本 ==="
cat /www/server/panel/class/common.py 2>/dev/null | grep -E "version" | head -2
ls /www/server/panel/ 2>/dev/null | grep -iE "version|info" | head -3
cat /www/server/panel/config/config.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('title:', d.get('title'), '| ip:', d.get('ip'), '| bind:', d.get('bind'))" 2>/dev/null || echo "config.json 解析失败"
