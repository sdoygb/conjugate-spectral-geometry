#!/bin/bash
echo "=== 1. admin_routes.py 行数 ==="
wc -l /usr/local/geometry-ai/admin_routes.py
echo ""
echo "=== 2. rebuild 相关行号 ==="
grep -n "rebuild" /usr/local/geometry-ai/admin_routes.py
echo ""
echo "=== 3. require_admin 定义位置 ==="
grep -rn "def require_admin" /usr/local/geometry-ai/*.py | head -3
echo ""
echo "=== 4. require_admin 实现 ==="
grep -rn -A 12 "def require_admin" /usr/local/geometry-ai/config.py 2>/dev/null | head -30
echo ""
echo "=== 5. .env 键名（仅键名） ==="
grep -oE "^[A-Za-z_]+" /usr/local/geometry-ai/.env 2>/dev/null
echo ""
echo "=== 6. admin_bp 挂载与 admin token 配置 ==="
grep -n "ADMIN_TOKEN\|admin_token\|X-Admin\|admin_key" /usr/local/geometry-ai/config.py /usr/local/geometry-ai/server.py 2>/dev/null | head -10
