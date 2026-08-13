#!/bin/bash
echo "=== 启动时间 ==="
uptime
echo ""
echo "=== 服务状态 ==="
systemctl is-active open-webui
systemctl is-active geometry-ai
systemctl is-active bt
echo ""
echo "=== 端口监听 ==="
ss -tln | grep -E ':8080|:17995|:22|:80' || echo "关键端口未监听"
echo ""
echo "=== open-webui 版本 ==="
curl -s --max-time 5 http://127.0.0.1:8080/api/version 2>/dev/null || echo "open-webui API 未响应"
