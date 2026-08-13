#!/bin/bash
echo "=== 1. db audio.stt 配置 ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:/usr/local/geometry-ai/webui_data/webui.db?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE 'audio.stt%'\")
for k, v in cur.fetchall():
    if 'api_key' in k:
        print(f'{k} = {v[:10]}...{v[-4:]}')
    else:
        print(f'{k} = {v!r}')
conn.close()
" 2>/dev/null

echo ""
echo "=== 2. transcribe() 开头（1070-1090） ==="
sed -n '1070,1090p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/routers/audio.py

echo ""
echo "=== 3. 服务 User/Group ==="
grep -E "^User=|^Group=" /etc/systemd/system/open-webui.service

echo ""
echo "=== 4. 最新用户测试完整日志（09:38:55-09:39:05） ==="
journalctl -u open-webui --since '09:38:55' --until '09:39:05' --no-pager 2>/dev/null | grep -vE 'version.json' | head -30
