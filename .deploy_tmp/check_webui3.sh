#!/bin/bash
echo "=== 进程 ==="
ps aux | grep -E "open.webui|open_webui" | grep -v grep | head -5
echo ""
echo "=== 8080 HTTP 响应 ==="
python3 -c "
import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:8080', timeout=5)
    print('HTTP', r.status)
    print('Server:', r.headers.get('Server'))
except Exception as e:
    print('ERR', type(e).__name__, e)
"
echo ""
echo "=== 查找 webui 数据文件 ==="
echo 'ab640815.' | sudo -S find / -name "webui.db" 2>/dev/null | head -5
echo 'ab640815.' | sudo -S ls -la /root/ 2>/dev/null | head -20
echo ""
echo "=== open-webui 最近日志 ==="
journalctl -u open-webui --no-pager -n 12 | tail -12
echo ""
echo "=== geometry-ai-webui 最近日志 ==="
journalctl -u geometry-ai-webui --no-pager -n 8 | tail -8
