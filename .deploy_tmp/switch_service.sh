#!/bin/bash
echo "=== 1. 当前 ExecStart/PATH ==="
grep -E "ExecStart|^Environment=\"?PATH" /etc/systemd/system/open-webui.service
echo ""
echo "=== 2. 备份 ==="
cp /etc/systemd/system/open-webui.service /root/open-webui.service.bak2_$(date +%Y%m%d%H%M%S)
echo "备份完成"
echo ""
echo "=== 3. 替换为新 venv ==="
sed -i 's|ExecStart=/usr/local/geometry-ai/venv/bin/open-webui|ExecStart=/usr/local/open-webui-venv/bin/open-webui|' /etc/systemd/system/open-webui.service
sed -i 's|PATH=/usr/local/geometry-ai/venv/bin|PATH=/usr/local/open-webui-venv/bin|' /etc/systemd/system/open-webui.service
grep -E "ExecStart|PATH=" /etc/systemd/system/open-webui.service
echo ""
echo "=== 4. daemon-reload + 重启 ==="
systemctl daemon-reload
systemctl restart open-webui
sleep 8
echo "open-webui: $(systemctl is-active open-webui)"
echo ""
echo "=== 5. 版本验证 ==="
/usr/local/open-webui-venv/bin/python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=10))
    print('API 版本:', r)
except Exception as e:
    print('ERR', type(e).__name__, e)
"
echo ""
echo "=== 6. 进程确认 ==="
ps aux | grep "open-webui serve" | grep -v grep | head -2 | awk '{print $2, $11, $12, $13}'
echo ""
echo "=== 7. 启动日志（错误检查） ==="
journalctl -u open-webui --no-pager --since "1 minute ago" | grep -iE "error|traceback|exception|fail" | head -8 || echo "无错误日志"
