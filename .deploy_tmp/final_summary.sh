#!/bin/bash
echo "=== config_old 表 rag 键（追溯 SentenceTransformer 错误来源） ==="
echo 'ab640815.' | sudo -S /usr/local/open-webui-venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/usr/local/geometry-ai/webui_data/webui.db')
conn.execute('PRAGMA query_only = ON')
try:
    rows = conn.execute(\"SELECT key, value FROM config_old WHERE key LIKE 'rag%' ORDER BY key\").fetchall()
    for k, v in rows:
        print(k, '=', v[:200])
except Exception as e:
    print('config_old 查询失败:', e)
conn.close()
" 2>/dev/null
echo ""
echo "=== 清理服务器临时脚本（含密码） ==="
echo 'ab640815.' | sudo -S rm -f /tmp/switch_service.sh /tmp/run_switch.sh /tmp/check_rag.sh /tmp/check_rag2.sh /tmp/check_rag3.sh /tmp/final_check.sh /tmp/retry_install.sh /tmp/retry_install2.sh /tmp/retry_install3.sh /tmp/retry_install4.sh /tmp/disk_test.sh /tmp/run_disk_test.sh /tmp/downgrade_chroma.sh /tmp/upgrade_webui.sh /tmp/run_upgrade.sh /tmp/create_venv.sh /tmp/run_venv.sh /tmp/bg_wait_install.sh /tmp/bg_wait_install2.sh /tmp/owui_install.log /tmp/owui_install2.log /tmp/owui_install3.log /tmp/owui_install4.log /tmp/install_wait.txt /tmp/install_wait2.txt /tmp/venv_setup.log 2>/dev/null
echo "清理完成"
ls /tmp/*.sh /tmp/owui_install* /tmp/install_wait* 2>/dev/null || echo "✅ 临时文件已全部清除"
echo ""
echo "=== 最终状态总览 ==="
echo "--- open-webui ---"
systemctl is-active open-webui
/usr/local/open-webui-venv/bin/python3 -c "
import urllib.request, json
r = json.load(urllib.request.urlopen('http://localhost:8080/api/version', timeout=8))
print('版本:', r['version'])
"
echo "--- geometry-ai ---"
systemctl is-active geometry-ai
python3 -c "
import urllib.request, json
r = json.load(urllib.request.urlopen('http://localhost:5000/health', timeout=8))
print('vector_kb:', r.get('vector_kb_initialized'), '| docs:', r.get('total_docs'))
"
echo "--- venv 隔离 ---"
echo "新 venv: $(/usr/local/open-webui-venv/bin/pip show open-webui 2>/dev/null | grep Version) | $(/usr/local/open-webui-venv/bin/pip show chromadb 2>/dev/null | grep Version)"
echo "共享 venv: $(/usr/local/geometry-ai/venv/bin/pip show chromadb 2>/dev/null | grep Version) | open-webui: $(/usr/local/geometry-ai/venv/bin/pip show open-webui 2>/dev/null | grep Version || echo 无)"
