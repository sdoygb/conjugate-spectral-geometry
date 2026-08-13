#!/bin/bash
echo "=== 1. db 完整 audio.stt 配置（只读） ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE 'audio.stt%'\")
for k, v in cur.fetchall():
    print(f'{k} = {v}')
conn.close()
" 2>&1
echo ""
echo "=== 2. WHISPER_LANGUAGE 定义 ==="
grep -n "WHISPER_LANGUAGE" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/env.py 2>/dev/null | head -3
echo ""
echo "=== 3. AIOHTTP_CLIENT_SESSION_SSL 定义 ==="
grep -n "AIOHTTP_CLIENT_SESSION_SSL" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/env.py 2>/dev/null | head -3
echo ""
echo "=== 4. systemd 环境中的 AUDIO/WHISPER/STT 变量 ==="
systemctl cat open-webui 2>/dev/null | grep -iE "AUDIO|WHISPER|STT" || echo "（无）"
