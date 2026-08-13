#!/bin/bash
echo "=== 1. 最新 Open WebUI 日志（最近20分钟） ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "20 min ago" --no-pager 2>/dev/null | grep -iE "transcrib|422|stt|audio|chunk|External|Converted|error" | tail -30
echo ""
echo "=== 2. 反代进程（Nginx/Caddy） ==="
ps aux | grep -E "nginx|caddy" | grep -v grep | head -5
echo ""
echo "=== 3. 监听端口 ==="
ss -tlnp 2>/dev/null | grep -E ":80 |:443 |:8080 " | head -10
echo ""
echo "=== 4. Nginx 配置关键项 ==="
echo 'ab640815.' | sudo -S nginx -T 2>/dev/null | grep -E "server_name|proxy_pass|client_max_body_size|listen" | head -40
echo ""
echo "=== 5. Caddy 配置（如有） ==="
cat /etc/caddy/Caddyfile 2>/dev/null | head -40
