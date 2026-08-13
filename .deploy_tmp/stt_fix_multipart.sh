#!/bin/bash
DB=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/webui.db
echo "=== 1. 备份 ==="
echo 'ab640815.' | sudo -S cp $DB ${DB}.bak_premultipart && echo "备份完成: ${DB}.bak_premultipart"

echo ""
echo "=== 2. 修改 api_request_format -> multipart ==="
echo 'ab640815.' | sudo -S python3 -c "
import sqlite3
conn = sqlite3.connect('$DB')
cur = conn.cursor()
cur.execute(\"UPDATE config SET value='\\\"multipart\\\"' WHERE key='audio.stt.openai.api_request_format'\")
conn.commit()
cur.execute(\"SELECT key, value FROM config WHERE key='audio.stt.openai.api_request_format'\")
print('确认:', cur.fetchone())
conn.close()
"

echo ""
echo "=== 3. 重启 open-webui ==="
echo 'ab640815.' | sudo -S systemctl restart open-webui
sleep 8
systemctl is-active open-webui
systemctl show open-webui --property=MainPID

echo ""
echo "=== 4. 复现测试（用最新 wav 直接调 transcribe） ==="
F=$(ls -t /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data/cache/audio/transcriptions/*.wav 2>/dev/null | head -1)
echo "测试文件: $F"
if [ -z "$F" ]; then
  echo "（无 wav 文件）"
  exit 0
fi
SECRET=$(systemctl cat open-webui 2>/dev/null | grep WEBUI_SECRET_KEY | head -1 | cut -d= -f2- | tr -d '"')
WEBUI_SECRET_KEY="$SECRET" OPENWEBUI_DATA_DIR=/usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/data \
  /usr/local/open-webui-venv/bin/python3 /tmp/run_transcribe.py "$F" 2>&1 | tail -15
