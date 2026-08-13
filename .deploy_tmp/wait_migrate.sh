#!/bin/bash
echo "=== 等待数据库迁移完成（最多 100 秒） ==="
for i in $(seq 1 20); do
  sleep 5
  V=$(python3 -c "
import urllib.request, json
try:
    print(json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=3)))
except Exception:
    print('')
" 2>/dev/null)
  if [ -n "$V" ]; then
    echo "迁移完成 (${i}x5s): $V"
    break
  fi
done
echo ""
echo "=== 启动日志尾部 ==="
journalctl -u open-webui --no-pager -n 15 | tail -10
echo ""
echo "=== 错误检查（3 分钟内） ==="
journalctl -u open-webui --no-pager --since "3 minutes ago" | grep -iE "error|traceback|exception|failed" | head -8 || echo "无错误"
echo ""
echo "=== 数据文件状态 ==="
ls -la /usr/local/geometry-ai/webui_data/webui.db* 2>/dev/null
