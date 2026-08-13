#!/bin/bash
echo "=== 1. python3.12 位置 ==="
which python3.12 || ls /usr/bin/python3.12 2>/dev/null || echo "无 python3.12"
echo ""
echo "=== 2. webui.db 中的 RAG 配置（存库配置会覆盖环境变量） ==="
python3 -c "
import sqlite3
db = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
rows = db.execute(\"SELECT key, value FROM config WHERE key LIKE '%rag%' OR key LIKE '%embedding%' OR key LIKE '%offline%'\").fetchall()
for k, v in rows:
    print(k, '=', str(v)[:100])
db.close()
"
echo ""
echo "=== 3. 建独立 venv ==="
/usr/bin/python3.12 -m venv /usr/local/open-webui-venv 2>&1 | tail -2
echo "venv 创建: $?"
/usr/local/open-webui-venv/bin/python3 --version
echo ""
echo "=== 4. 后台安装 open-webui 0.11.0（独立 venv） ==="
nohup /usr/local/open-webui-venv/bin/pip install open-webui==0.11.0 > /tmp/openwebui_venv_install.log 2>&1 &
echo "PIP_PID=$!"
sleep 5
head -5 /tmp/openwebui_venv_install.log
