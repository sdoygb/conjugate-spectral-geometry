#!/bin/bash
echo "=== 数据库 rag 配置（root 查询） ==="
echo 'ab640815.' | sudo -S /usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
conn.execute('PRAGMA query_only = ON')
rows = conn.execute(\"SELECT key, value FROM config WHERE key LIKE 'rag%' ORDER BY key\").fetchall()
for k, v in rows:
    print(k, '=', v[:200])
conn.close()
" 2>/dev/null
echo ""
echo "=== 数据表概况 ==="
echo 'ab640815.' | sudo -S /usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
conn.execute('PRAGMA query_only = ON')
tables = [r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
print('tables:', tables)
for t in ['rag_documents', 'file']:
    if t in tables:
        cnt = conn.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0]
        print(t, 'count:', cnt)
conn.close()
" 2>/dev/null
echo ""
echo "=== open-webui 启动后 RAG 相关日志（全量） ==="
journalctl -u open-webui --no-pager --since "08:05:00" | grep -icE "sentence|embedding|rag|retriev" 
journalctl -u open-webui --no-pager --since "08:05:00" | grep -iE "sentence|embedding|rag|retriev" | tail -5
