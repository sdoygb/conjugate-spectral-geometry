#!/bin/bash
echo "=== 1. 最新 STT 日志（最近30分钟，含完整上下文） ==="
echo 'ab640815.' | sudo -S journalctl -u open-webui --since "30 min ago" --no-pager 2>/dev/null | grep -iE "transcrib|422|stt|audio|chunk|External|Converted|ffprobe|ffmpeg|Traceback|Error" | tail -50
echo ""
echo "=== 2. webui.db audio.stt 配置（只读） ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE 'audio.stt%'\")
for k, v in cur.fetchall():
    if 'api_key' in k:
        print(f'{k} = {v[:8]}...{v[-4:]} (len={len(v)})')
    else:
        print(f'{k} = {v}')
conn.close()
"
echo ""
echo "=== 3. 修复代码确认 ==="
grep -n "audio_data\|audio_chunks" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py | head -10
echo ""
echo "=== 4. pyc 缓存与源文件时间 ==="
ls -la /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py
ls -la /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/__pycache__/audio*.pyc 2>/dev/null
echo ""
echo "=== 5. open-webui 服务状态与进程 ==="
systemctl show open-webui --property=ActiveEnterTimestamp,MainPID 2>/dev/null
ps aux | grep -E "open_webui|uvicorn|gunicorn" | grep -v grep | head -5
