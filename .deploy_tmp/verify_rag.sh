#!/bin/bash
echo "=== 1. webui.db config 表 RAG 配置 ==="
python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
rows = conn.execute(\"SELECT key, value FROM config WHERE key LIKE 'rag%'\").fetchall()
if rows:
    for k, v in rows:
        print(k, '=', str(v)[:110])
else:
    print('config 表无 rag 键')
conn.close()
"
echo ""
echo "=== 2. open-webui 进程环境变量（RAG/WEBUI 相关） ==="
PID=$(pgrep -f "open-webui serve" | head -1)
echo "PID: $PID"
tr '\0' '\n' < /proc/$PID/environ 2>/dev/null | grep -E "^RAG|^OPENWEBUI|^WEBUI|^ENABLE|^OFFLINE" | head -15
echo ""
echo "=== 3. 日志中 SentenceTransformer 检查（15 分钟） ==="
journalctl -u open-webui --no-pager --since "15 minutes ago" | grep -i "sentence" | head -5
if [ $? -ne 0 ]; then echo "无 SentenceTransformer 错误"; fi
echo ""
echo "=== 4. 日志中检索/知识库活动 ==="
journalctl -u open-webui --no-pager --since "15 minutes ago" | grep -iE "retriev|knowledge|collection" | head -8
if [ $? -ne 0 ]; then echo "无检索记录（服务刚迁移完，正常）"; fi
