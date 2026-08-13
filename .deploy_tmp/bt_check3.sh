#!/bin/bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
echo "=== 1. 浏览器 UA 访问安全入口 ==="
curl -A "$UA" -s -o /dev/null -w "HTTP %{http_code} (redirect: %{redirect_url})\n" --max-time 5 http://127.0.0.1:17995/sdoygb
echo ""
echo "=== 2. 浏览器 UA 访问根路径 ==="
curl -A "$UA" -s -o /dev/null -w "HTTP %{http_code} (redirect: %{redirect_url})\n" --max-time 5 http://127.0.0.1:17995/
echo ""
echo "=== 3. bind.pl 内容（IP 访问限制） ==="
cat /www/server/panel/data/bind.pl 2>/dev/null | head -20
echo "--- 文件详情 ---"
ls -la /www/server/panel/data/bind.pl 2>/dev/null
echo ""
echo "=== 4. admin_path.pl 原始内容（hexdump） ==="
xxd /www/server/panel/data/admin_path.pl 2>/dev/null | head -3
echo ""
echo "=== 5. 访问入口后的跳转目标 ==="
curl -A "$UA" -s -L -o /dev/null -w "final: HTTP %{http_code} url: %{url_effective}\n" --max-time 8 http://127.0.0.1:17995/sdoygb
echo ""
echo "=== 6. 面板 08:24 后日志（有无近期错误） ==="
grep -c "Traceback" /www/server/panel/logs/error.log 2>/dev/null
tail -5 /www/server/panel/logs/error.log 2>/dev/null | grep -E "Error|error" | head -3
echo ""
echo "=== 7. 面板入口文件（index） ==="
ls /www/server/panel/*.py 2>/dev/null | head -5
grep -E "admin_path|安全入口" /www/server/panel/class/public.py 2>/dev/null | head -3
