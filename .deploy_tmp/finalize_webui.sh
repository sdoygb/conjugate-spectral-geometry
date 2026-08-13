#!/bin/bash
echo "=== 0. 新 venv open-webui 可执行文件检查 ==="
ls -la /usr/local/open-webui-venv/bin/open-webui 2>/dev/null || echo "MISSING!"
echo ""
echo "=== 1. 当前 service 关键行 ==="
grep -E "ExecStart|PATH=" /etc/systemd/system/open-webui.service
echo ""
echo "=== 2. 修改 ExecStart 指向新 venv ==="
sed -i 's|ExecStart=/usr/local/geometry-ai/venv/bin/open-webui|ExecStart=/usr/local/open-webui-venv/bin/open-webui|' /etc/systemd/system/open-webui.service
sed -i 's|ExecStart=/usr/local/geometry-ai/venv/bin/python3 -m open_webui|ExecStart=/usr/local/open-webui-venv/bin/open-webui|' /etc/systemd/system/open-webui.service
echo "=== 3. 修改 PATH ==="
sed -i 's|PATH=/usr/local/geometry-ai/venv/bin|PATH=/usr/local/open-webui-venv/bin|' /etc/systemd/system/open-webui.service
echo ""
echo "=== 4. 修改后确认 ==="
grep -E "ExecStart|PATH=" /etc/systemd/system/open-webui.service
echo ""
echo "=== 5. daemon-reload + restart ==="
systemctl daemon-reload
systemctl restart open-webui
sleep 15
echo "服务状态: $(systemctl is-active open-webui)"
echo ""
echo "=== 6. 版本验证 ==="
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=10))
    print('版本:', r)
except Exception as e:
    print('ERR', type(e).__name__, e)
"
echo ""
echo "=== 7. 进程确认 ==="
ps aux | grep -E "open-webui|open_webui" | grep -v grep | head -2
echo ""
echo "=== 8. 启动日志关键行 ==="
journalctl -u open-webui --no-pager -n 50 | grep -iE "error|sentence|rag|started|running|uvicorn|version" | head -12
