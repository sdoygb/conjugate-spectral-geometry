#!/bin/bash
echo "=== 1. require_admin 实现（admin_routes.py 25-60行） ==="
sed -n '25,60p' /usr/local/geometry-ai/admin_routes.py
echo ""
echo "=== 2. server.py rebuild 端点（595-660行） ==="
sed -n '595,660p' /usr/local/geometry-ai/server.py
echo ""
echo "=== 3. server.py /v1/vector/rebuild（865-940行） ==="
sed -n '865,940p' /usr/local/geometry-ai/server.py
