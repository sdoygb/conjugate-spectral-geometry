#!/bin/bash
echo "=== session_pool.py 完整内容（1-130行） ==="
sed -n '1,130p' /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/utils/session_pool.py
echo ""
echo "=== ENABLE_FORWARD_USER_INFO_HEADERS 定义 ==="
grep -rn "ENABLE_FORWARD_USER_INFO_HEADERS" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/ 2>/dev/null | grep -v ".pyc" | head -5
echo ""
echo "=== include_user_info_headers 定义 ==="
grep -rn "def include_user_info_headers" /usr/local/open-webui-venv/lib/python3.12/site-packages/open_webui/ 2>/dev/null | head -3
