#!/bin/bash
echo "=== 1. open-webui 服务实际 DATA_DIR ==="
systemctl cat open-webui 2>/dev/null | grep -E "Environment|ExecStart" | head -10

echo ""
echo "=== 2. 包内 data 目录 ==="
ls -la /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/ 2>/dev/null | head -15

echo ""
echo "=== 3. 所有可能的 webui.db ==="
echo 'ab640815.' | sudo -S find /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data /usr/local/geometry-ai -name "webui.db" 2>/dev/null | head -10

echo ""
echo "=== 4. 包内 db 的 STT 配置（如果存在） ==="
DB=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db
if [ -f "$DB" ]; then
  echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('file:$DB?mode=ro', uri=True)
cur = conn.cursor()
cur.execute(\"SELECT key, value FROM config WHERE key LIKE 'audio.stt%'\")
for k, v in cur.fetchall():
    if 'api_key' in k:
        print(f'{k} = {v[:12]}...{v[-4:]}')
    else:
        print(f'{k} = {v!r}')
conn.close()
" 2>/dev/null
else
  echo "（包内无 webui.db）"
fi
