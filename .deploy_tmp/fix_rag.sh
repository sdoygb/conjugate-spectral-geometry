#!/bin/bash
echo "=== 1. 备份 webui.db ==="
cp /usr/local/geometry-ai/webui_data/webui.db /root/webui_backup_20260812_ragfix.db
echo "备份: /root/webui_backup_20260812_ragfix.db"
echo ""
echo "=== 2. 修正 RAG embedding 配置 ==="
python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
c = conn.cursor()
c.execute(\"UPDATE config SET value='openai' WHERE key='rag.embedding_engine'\")
c.execute(\"UPDATE config SET value='BAAI/bge-m3' WHERE key='rag.embedding_model'\")
conn.commit()
for row in c.execute(\"SELECT key, value FROM config WHERE key IN ('rag.embedding_engine','rag.embedding_model')\").fetchall():
    print(row[0], '=', row[1])
conn.close()
"
echo ""
echo "=== 3. 重启 open-webui ==="
systemctl restart open-webui
sleep 15
echo "状态: $(systemctl is-active open-webui)"
python3 -c "
import urllib.request, json
try:
    r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=8))
    print('版本:', r.get('version'))
except Exception as e:
    print('ERR', type(e).__name__)
"
echo ""
echo "=== 4. 重启后日志错误检查 ==="
journalctl -u open-webui --no-pager --since "1 minute ago" | grep -iE "error|traceback|exception|sentence" | head -6
if [ $? -ne 0 ]; then echo "无错误"; fi
