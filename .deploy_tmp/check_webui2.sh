#!/bin/bash
echo "=== 服务启用/运行状态 ==="
systemctl is-enabled open-webui 2>&1; systemctl is-active open-webui 2>&1
systemctl is-enabled geometry-ai-webui 2>&1; systemctl is-active geometry-ai-webui 2>&1
echo ""
echo "=== 数据目录（root 用户） ==="
echo 'ab640815.' | sudo -S ls -la /root/.open-webui 2>/dev/null | head -10 || echo "无 /root/.open-webui"
echo ""
echo "=== 数据目录（sdoygb 用户） ==="
ls -la /home/sdoygb/.open-webui 2>/dev/null | head -10 || echo "无 /home/sdoygb/.open-webui"
echo ""
echo "=== 数据卷大小 ==="
echo 'ab640815.' | sudo -S du -sh /root/.open-webui 2>/dev/null || echo "root 卷 n/a"
du -sh /home/sdoygb/.open-webui 2>/dev/null || echo "sdoygb 卷 n/a"
echo ""
echo "=== venv 里 open-webui 文件位置 ==="
ls -la /usr/local/geometry-ai/venv/lib/python3*/site-packages/ 2>/dev/null | grep -i open_webui | head -3
